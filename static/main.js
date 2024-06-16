function deletePosition(reqNum) {
    if (confirm("Are you sure you want to delete " + reqNum + "? This will permanently delete the position.")) {
        fetch(`/delete_position/${reqNum}`, {
            method: 'POST',
        })
        .then(response => {
            if (response.ok) {
                var row = document.querySelector(`tr td:first-child:contains("${reqNum}")`).parentNode;
                row.remove();
                if (document.querySelectorAll('tbody tr').length === 0) {
                    window.location.reload();  // Reload if no rows left
                }
            } else {
                alert("Failed to delete the position. Please try again.");
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert("An error occurred. Please try again.");
        });
    }
}

// Custom selector for "contains" functionality
jQuery.expr[':'].contains = function(a, i, m) {
    return jQuery(a).text().toUpperCase()
        .indexOf(m[3].toUpperCase()) >= 0;
};