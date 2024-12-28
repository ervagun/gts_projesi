$(document).ready(function() {   
    $("#id").prepend("<option value=''>&nbsp;</option>");

    $(".chosen-select").chosen({
        no_results_text: "Oops, nothing found!"
    });
});

// Script for changing institute options according to university selection 
$(document).ready(function() {
    $("#uni").change(function() {
        var uni_id = $(this).val();
        var options = '';
        for (var i = 0; i < institute_list.length; i++) {
            if (institute_list[i][2] == uni_id) {
                options += '<option value="' + institute_list[i][0] + '">' + institute_list[i][1] + '</option>';
            }
        }
        $("#ins").html(options);
    });
});

// Countdown function for page redirection
function countdown() {
    var i = document.getElementById('counter');
    if (parseInt(i.innerHTML) <= 0) {
        location.href = '/';
        return;
    }
    i.innerHTML = parseInt(i.innerHTML) - 1;
}
setInterval(function() {
    countdown();
}, 1000);

// Script for adding empty option to the beginning of the select options
$(document).ready(function() {   
    $("#author").prepend("<option value=''>&nbsp;</option>");
    $("#supervisors").prepend("<option value=''>&nbsp;</option>");
    $("#cosupervisors").prepend("<option value=''>&nbsp;</option>");
    $("#topics").prepend("<option value=''>&nbsp;</option>");
    $("#keywords").prepend("<option value=''>&nbsp;</option>");
    $("#uni").prepend("<option value=''>&nbsp;</option>");
    $("#ins").prepend("<option value=''>&nbsp;</option>");
    $("#type").prepend("<option value=''>&nbsp;</option>");
    $("#language").prepend("<option value=''>&nbsp;</option>");

    $(".chosen-select").chosen({
        no_results_text: "Oops, nothing found!"
    });
});

// Function to handle search for thesis by number
function searchThesisByNumber() {
    // Get the thesis number from the input
    var thesisNumber = document.getElementById('thesis_id').value;
    
    // Redirect to the thesis detail page with the given thesis number
    window.location.href = '/get_thesis/' + thesisNumber;
}

