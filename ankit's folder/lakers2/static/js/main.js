
function showModal(modalId) {
    var modal = document.getElementById(modalId);
    modal.style.display = "block";
}


document.addEventListener('DOMContentLoaded', function() {
    // Retrieve all close buttons
    var closeButtons = document.getElementsByClassName("close");

    
    Array.from(closeButtons).forEach(function(button) {
        button.onclick = function() {
            // Using `this.closest('.modal')` to find the parent modal of the close button
            var modal = this.closest('.modal1');
            if (modal) {
                modal.style.display = "none";
            }
        }
    });

    window.onclick = function(event) {
        
        if (event.target.classList.contains('modal1')) {
            
            event.target.style.display = "none";
        }
    };
});
