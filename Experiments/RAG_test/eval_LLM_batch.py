import argparse
import json
import logging
import os
import time
from glob import glob

import pandas as pd
from dotenv import load_dotenv
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_pinecone import PineconeVectorStore
from langchain_upstage import ChatUpstage, UpstageEmbeddings
from pydantic import BaseModel, Field
from sklearn.metrics import (accuracy_score, confusion_matrix, f1_score,
                             precision_score, recall_score)
from tqdm import tqdm

logging.basicConfig(filename="evaluation.log", level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


class EvalResponse(BaseModel):
    responses: list[str] = Field(description="List of responses ('O' or 'X') for each statement")


def batch_eval_model(
    model: ChatUpstage, test_data: pd.DataFrame, vector_store: PineconeVectorStore, k: int, batch_size: int = 10
):
    start_time = time.time()

    parser = JsonOutputParser(pydantic_object=EvalResponse)

    # Create batch prompts
    vanilla_prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                """You are a helpful AI that evaluates factual accuracy of multiple statements.
        For each statement, respond with 'O' if the statement is factual or 'X' if not.
        Your response should be a list of 'O' or 'X' corresponding to each statement in order.

        Please respond in the following format:
        {format_instructions}
        """,
            ),
            ("user", "Statements:\n{statements}\nEvaluate if these statements are factual."),
        ]
    )

    rag_prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                """You are a helpful AI that evaluates factual accuracy of multiple statements using provided contexts.
        For each statement, respond with 'O' if the statement is factual or 'X' if not based on its corresponding context.
        Your response should be a list of 'O' or 'X' corresponding to each statement in order.

        Please respond in the following format:
        {format_instructions}
        """,
            ),
            (
                "user",
                "Context and Statements:\n{context_statements}\nEvaluate if these statements are factual based on their contexts.",
            ),
        ]
    )

    results = []
    error_count = 0

    # Process data in batches
    for start_idx in tqdm(range(0, len(test_data), batch_size)):
        batch_df = test_data.iloc[start_idx : start_idx + batch_size]
        max_retries = 3

        for attempt in range(max_retries):
            try:
                if isinstance(model, str) and model == "vanilla":
                    # Format multiple statements
                    statements = "\n".join(
                        [f"{i+1}. {row['statement']}" for i, row in enumerate(batch_df.itertuples())]
                    )

                    chain = vanilla_prompt | model | parser
                    response = chain.invoke(
                        {"statements": statements, "format_instructions": parser.get_format_instructions()}
                    )
                    batch_assessments = response["responses"]

                else:
                    # Get contexts for all statements in batch
                    context_statements = []
                    for _, row in batch_df.iterrows():
                        similar_docs = vector_store.similarity_search(row["statement"], k=k)
                        context = "\n".join([doc.page_content for doc in similar_docs])
                        context_statements.append(f"Context: {context}\nStatement: {row['statement']}")

                    formatted_input = "\n\n".join([f"{i+1}. {cs}" for i, cs in enumerate(context_statements)])

                    chain = rag_prompt | model | parser
                    response = chain.invoke(
                        {"context_statements": formatted_input, "format_instructions": parser.get_format_instructions()}
                    )
                    batch_assessments = response["responses"]

                # Add results for the batch
                for (_, row), assessment in zip(batch_df.iterrows(), batch_assessments):
                    results.append(
                        {
                            "source": row["source"],
                            "page_num": row["page_num"],
                            "statement": row["statement"],
                            "feedback": row["feedback"],
                            "model_assessment": assessment,
                            "retry_count": attempt,
                        }
                    )
                break

            except Exception as e:
                error_count += 1
                logging.error(f"Error on attempt {attempt + 1} for batch starting at {start_idx}: {e}")
                if attempt == max_retries - 1:
                    # On final retry failure, mark all batch items as 'X'
                    for _, row in batch_df.iterrows():
                        results.append(
                            {
                                "source": row["source"],
                                "page_num": row["page_num"],
                                "statement": row["statement"],
                                "feedback": row["feedback"],
                                "model_assessment": "X",
                                "retry_count": attempt + 1,
                            }
                        )
                time.sleep(1)

        time.sleep(0.5)  # Rate limiting between batches

    end_time = time.time()
    execution_time = end_time - start_time

    # Create results DataFrame and calculate metrics
    results_df = pd.DataFrame(results)

    y_true = [1 if x == "O" else 0 for x in results_df["feedback"]]
    y_pred = [1 if x == "O" else 0 for x in results_df["model_assessment"]]

    metrics = {
        "execution_time": execution_time,
        "total_samples": len(results_df),
        "error_rate": error_count / len(results_df),
        "average_retries": results_df["retry_count"].mean(),
        "accuracy": accuracy_score(y_true, y_pred),
        "precision": precision_score(y_true, y_pred),
        "recall": recall_score(y_true, y_pred),
        "f1": f1_score(y_true, y_pred),
    }

    # Calculate confusion matrix
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred).ravel()
    confusion_metrics = {
        "true_negatives": tn,
        "false_positives": fp,
        "false_negatives": fn,
        "true_positives": tp,
        "specificity": tn / (tn + fp) if (tn + fp) > 0 else 0,
        "npv": tn / (tn + fn) if (tn + fn) > 0 else 0,
    }
    metrics.update(confusion_metrics)

    # Log results
    logging.info(f"\n{'='*50}\nEvaluation Results\n{'='*50}")
    logging.info(f"Model Type: {'Vanilla' if isinstance(model, str) and model == 'vanilla' else 'RAG'}")
    logging.info(f"Total Execution Time: {execution_time:.2f} seconds")
    logging.info(f"Average Time per Sample: {execution_time/len(results_df):.2f} seconds")
    logging.info(f"Average Time per Batch: {execution_time/(len(results_df)/batch_size):.2f} seconds")

    logging.info("\nOverall Metrics:")
    for metric, value in metrics.items():
        logging.info(f"{metric}: {value:.4f}")

    # Save detailed results
    timestamp = time.strftime("%Y%m%d-%H%M%S")

    if not os.path.exists("results"):
        os.makedirs("results")
    results_df.to_csv(f"results/evaluation_results_{timestamp}.csv", index=False)

    return results_df, metrics


def save_results_to_txt(file_name, args, metrics, output_file="experiment_results.txt"):
    base_file_name = os.path.basename(file_name)
    result_line = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "file_name": base_file_name,
        "args": vars(args),
        "metrics": {
            "accuracy": metrics["accuracy"],
            "precision": metrics["precision"],
            "recall": metrics["recall"],
            "f1": metrics["f1"],
            "execution_time": metrics["execution_time"],
        },
    }
    result_str = json.dumps(result_line, ensure_ascii=False)
    with open(output_file, "a", encoding="utf-8") as f:
        f.write(result_str + "\n")


def main(args):
    llm_upstage = ChatUpstage(model="solar-pro", temperature=0)
    embeddings_query = UpstageEmbeddings(model="embedding-query")
    vector_store = PineconeVectorStore.from_existing_index(
        index_name=args.index_name,
        embedding=embeddings_query,
        namespace=args.namespace,
    )

    files = glob(args.data_path)
    for file in files:
        test_data = pd.read_csv(file)
        _, metrics = batch_eval_model(llm_upstage, test_data, vector_store, args.k, batch_size=args.batch_size)
        save_results_to_txt(file, args, metrics)


if __name__ == "__main__":
    load_dotenv()
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", type=str, default="vanilla")
    parser.add_argument("--data_path", type=str, default="OX/*.csv")
    parser.add_argument("--index_name", type=str, default="test-pre")
    parser.add_argument("--namespace", type=str, default="500-150")
    parser.add_argument("--k", type=int, default=1)
    parser.add_argument("--batch_size", type=int, default=10)
    args = parser.parse_args()
    main(args)
