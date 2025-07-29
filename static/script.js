document.addEventListener('DOMContentLoaded', function() {
    const graduation = document.getElementById('graduation');
    const subjectDiv = document.getElementById('subject');
    const rooms = document.querySelectorAll('input[name="rooms"]');
    const roomDetails = document.getElementById('room_details');
    const disabledMember = document.querySelectorAll('input[name="disabled_member"]');
    const disabledDetails = document.getElementById('disabled_details');

    if (graduation) {
        graduation.addEventListener('change', function() {
            subjectDiv.style.display = this.checked ? 'block' : 'none';
        });
    }

    rooms.forEach(room => {
        room.addEventListener('change', function() {
            roomDetails.style.display = this.value === 'Yes' ? 'block' : 'none';
        });
    });

    disabledMember.forEach(member => {
        member.addEventListener('change', function() {
            disabledDetails.style.display = this.value === 'Yes' ? 'block' : 'none';
        });
    });
});
