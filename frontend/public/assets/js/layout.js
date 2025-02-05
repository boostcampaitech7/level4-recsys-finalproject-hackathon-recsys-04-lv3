document.addEventListener("DOMContentLoaded", function () {
    loadComponent("header", "components/header.html");
    loadComponent("footer", "components/footer.html");
});

function loadComponent(elementId, filePath) {
    fetch(filePath)
        .then(response => response.text())
        .then(data => document.getElementById(elementId).innerHTML = data)
        .catch(error => console.error(`Error loading ${filePath}:`, error));
}
