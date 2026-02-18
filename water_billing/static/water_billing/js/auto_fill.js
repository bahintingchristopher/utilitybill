document.addEventListener('DOMContentLoaded', function() {
    const tenantInput = document.querySelector('#id_tenant_name');
    const roomInput = document.querySelector('#id_room_number');
    const prevInput = document.querySelector('#id_previous_reading');

    function performFill(nameValue) {
        if (!nameValue) return;

        let fetchUrl = window.location.pathname.includes('electricbill') 
            ? '/electric/get-tenant-data/' 
            : '/water/get-tenant-data/';

        fetch(`${fetchUrl}?name=${encodeURIComponent(nameValue)}`)
            .then(response => response.json())
            .then(data => {
                if (data.previous_reading !== undefined) {
                    // Update fields
                    roomInput.value = data.room_number || roomInput.value;
                    prevInput.value = data.previous_reading;
                    console.log("Values updated to: " + data.previous_reading);
                }
            });
    }

    if (tenantInput) {
        // Trigger on Name change
        tenantInput.addEventListener('blur', function() {
            performFill(this.value);
        });
    }

    // CHECK: Is there anything else in your file that mentions 'room_number'?
    // If you have a roomInput.addEventListener('blur'...) that sets value to 125, DELETE IT.
});