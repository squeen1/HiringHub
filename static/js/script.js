var modal = document.getElementById("interviewNotesModal");

function openModal(applicantName, reqNumber) {
    modal.style.display = "block";

    // Load interview notes for the specific applicant and requisition
    var xhr = new XMLHttpRequest();
    xhr.open("GET", "/load_interview_notes?applicant_name=" + applicantName + "&req_number=" + reqNumber, true);
    xhr.onreadystatechange = function() {


        if (xhr.readyState === XMLHttpRequest.DONE && xhr.status === 200) {
            var interviewNotesContainer = document.getElementById("interviewNotesContainer");
            interviewNotesContainer.innerHTML = xhr.responseText;
        }
    };
    xhr.send();
}

function closeModal() {
    modal.style.display = "none";
}

window.onclick = function(event) {
    if (event.target == modal) {
        modal.style.display = "none";
    }
}

function openResumeModal(filename) {
    if (filename) {
        var modal = document.getElementById('resumeModal');
        var iframe = document.getElementById('resumeFrame');
        iframe.src = '/resume/' + filename;
        iframe.onerror = function() {
            alert('Error loading the resume. The file may not exist.');
        };
        modal.style.display = 'block';
    } else {
        alert('No resume available for this applicant.');
    }
}

function closeResumeModal() {
    var modal = document.getElementById('resumeModal');
    var iframe = document.getElementById('resumeFrame');
    iframe.src = '';
    modal.style.display = 'none';
}


//filtering and sorting function - required to not have to reload the page each time
    document.getElementById('filter-sort-form').addEventListener('submit', function(event) {
        event.preventDefault();
        const filterBy = document.getElementById('filter_by').value;
        const filterValue = document.getElementById('filter_value').value;
        const sortBy = document.getElementById('sort_by').value;
        const order = document.getElementById('order').value;
        const url = new URL(window.location.href);
        url.searchParams.set('filter_by', filterBy);
        url.searchParams.set('filter_value', filterValue);
        url.searchParams.set('sort_by', sortBy);
        url.searchParams.set('order', order);
        window.location.href = url.toString();
    });
