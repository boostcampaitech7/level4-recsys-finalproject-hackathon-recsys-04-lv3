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

# Set up logging
logging.basicConfig(filename="evaluation.log", level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


def save_results_to_txt(file_name, args, metrics, output_file="experiment_results.txt"):
    """Save experiment results to a txt file"""
    # Extract base filename without path
    base_file_name = os.path.basename(file_name)

    # Create a single line with key information
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

    # Convert to JSON string
    result_str = json.dumps(result_line, ensure_ascii=False)

    # Append to file
    with open(output_file, "a", encoding="utf-8") as f:
        f.write(result_str + "\n")


class EvalResponse(BaseModel):
    factual: str = Field(description="Whether the statement is factual ('O') or not ('X')")


def eval_model(model: ChatUpstage, test_data: pd.DataFrame, vector_store: PineconeVectorStore, k: int):
    start_time = time.time()

    # Initialize JSON parser
    parser = JsonOutputParser(pydantic_object=EvalResponse)

    # Create prompt template for vanilla evaluation
    vanilla_prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                """You are a helpful AI that evaluates factual accuracy of statements.
        Respond with 'O' if the statement is factual or 'X' if not, and provide reasoning.
        Your response should strictly follow the format specified.

        Please respond in the following format:
        {format_instructions}
        """,
            ),
            ("user", "Statement: {statement}\nEvaluate if this statement is factual."),
        ]
    )

    # Create prompt template for RAG evaluation
    rag_prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                """You are a helpful AI that evaluates factual accuracy of statements using provided context.
        Respond with 'O' if the statement is factual or 'X' if not, and provide reasoning.
        Your response should strictly follow the format specified.

        Please respond in the following format:
        {format_instructions}
        """,
            ),
            (
                "user",
                "Context: {context}\nStatement: {statement}\nEvaluate if this statement is\
                    factual based on the provided context.",
            ),
        ]
    )

    results = []
    error_count = 0

    for idx, row in tqdm(test_data.iterrows(), total=len(test_data)):
        max_retries = 3
        for attempt in range(max_retries):
            try:
                if isinstance(model, str) and model == "vanilla":
                    chain = vanilla_prompt | model | parser
                    response = chain.invoke(
                        {"statement": row["statement"], "format_instructions": parser.get_format_instructions()}
                    )
                else:
                    similar_docs = vector_store.similarity_search(row["statement"], k=k)
                    context = "\n".join([doc.page_content for doc in similar_docs])

                    chain = rag_prompt | model | parser
                    response = chain.invoke(
                        {
                            "context": context,
                            "statement": row["statement"],
                            "format_instructions": parser.get_format_instructions(),
                        }
                    )
                results.append(
                    {
                        "source": row["source"],
                        "page_num": row["page_num"],
                        "statement": row["statement"],
                        "feedback": row["feedback"],
                        "model_assessment": response["factual"],
                        "retry_count": attempt,
                    }
                )
                break

            except Exception as e:
                error_count += 1
                logging.error(f"Error on attempt {attempt + 1} for statement {idx}: {e}")
                if attempt == max_retries - 1:
                    results.append(
                        {
                            "source": row["source"],
                            "page_num": row["page_num"],
                            "statement": row["statement"],
                            "feedback": row["feedback"],
                            "model_assessment": "X",  # Default to X on error
                            "retry_count": attempt + 1,
                        }
                    )
                time.sleep(1)

        time.sleep(0.5)  # Rate limiting

    end_time = time.time()
    execution_time = end_time - start_time

    # Create results DataFrame
    results_df = pd.DataFrame(results)

    # Calculate metrics
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
        "npv": tn / (tn + fn) if (tn + fn) > 0 else 0,  # Negative Predictive Value
    }
    metrics.update(confusion_metrics)

    # Log results
    logging.info(f"\n{'='*50}\nEvaluation Results\n{'='*50}")
    logging.info(f"Model Type: {'Vanilla' if isinstance(model, str) and model == 'vanilla' else 'RAG'}")
    logging.info(f"Total Execution Time: {execution_time:.2f} seconds")
    logging.info(f"Average Time per Sample: {execution_time/len(results_df):.2f} seconds")

    logging.info("\nOverall Metrics:")
    for metric, value in metrics.items():
        logging.info(f"{metric}: {value:.4f}")

    # Save detailed results
    timestamp = time.strftime("%Y%m%d-%H%M%S")
    # results folder
    if not os.path.exists("results"):
        os.makedirs("results")
    results_df.to_csv(f"results/evaluation_results_{timestamp}.csv", index=False)

    return results_df, metrics


def main(args):
    llm_upstage = ChatUpstage(model="solar-pro", temperature=0)
    embeddings_query = UpstageEmbeddings(model="embedding-query")  # 4096
    vector_store = PineconeVectorStore.from_existing_index(
        index_name=args.index_name,
        embedding=embeddings_query,
        namespace=args.namespace,
    )

    files = glob(args.data_path)
    for file in files:
        test_data = pd.read_csv(file)  # source,page_num,statement,feedback
        _, metrics = eval_model(llm_upstage, test_data, vector_store, args.k)
        # Save results to txt file
        save_results_to_txt(file, args, metrics)


if __name__ == "__main__":
    load_dotenv()
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", type=str, default="RAG")
    parser.add_argument("--data_path", type=str, default="OX/*.csv")
    parser.add_argument("--index_name", type=str, default="test-pre")
    parser.add_argument("--namespace", type=str, default="500-150")
    parser.add_argument("--k", type=int, default=1)
    args = parser.parse_args()
    main(args)
