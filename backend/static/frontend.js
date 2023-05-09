function docReady(fn) {
    // see if DOM is already available
    if (document.readyState === "complete" || document.readyState === "interactive") {
        // call on next available tick
        setTimeout(fn, 1);
    } else {
        document.addEventListener("DOMContentLoaded", fn);
    }
}


async function processQrCode(qrcode) {
    let json = await fetch( window.location.origin + "/scan_bin_qrcode", {
                method: "POST",
                body: JSON.stringify({
                    qrcode: `${qrcode}`,
                }),
                headers: {
                    "Content-type": "application/json; charset=UTF-8"
                }
            }).then((response) => response.json())
                .then(function(json){
                    return json;
                });

    // Display scan result
    var valid = false;
    if (!json.bin_online) {
        // Invalid QR code or bin is offline
        Bulma().alert({
            type: 'danger',
            title: 'Recycling bin offline',
            body: 'The scanned QR code is invalid or the recycling bin is offline.',
            confirm: 'OK'
        });
    }
    else if (!json.bin_available)
        // Bin online not available
        Bulma().alert({
            type: 'danger',
            title: 'Recycling bin unavailable',
            body: 'The scanned recycling bin is currently not available!',
            confirm: 'OK'
        });
    else {
        // Bin online and available
        Bulma().alert({
            type: 'success',
            title: 'QR Code Scanned',
            body: 'QR Code for bin 1234 successfully scanned, you may place containers in bin.',
            confirm: 'OK'
        });
        valid = true;
    }

    while (document.getElementsByClassName('modal-card').length !== 0) {
           await new Promise(r => setTimeout(r, 200));
    }

    return valid;
}

async function stopSessionOnBackend() {
    let json = await fetch(window.location.origin + "/stop_session")
                            .then((response) => {
                                return response.json();
                            })

    return !!json.success;
}

// Square QR box with edge size = 90% of the smaller edge of the viewfinder.
let qrboxSizeFunction = function(viewfinderWidth, viewfinderHeight) {
    let minEdgePercentage = 0.9;
    let minEdgeSize = Math.min(viewfinderWidth, viewfinderHeight);
    let qrboxSize = Math.floor(minEdgeSize * minEdgePercentage);
    return {
        width: qrboxSize,
        height: qrboxSize
    };
}

function loadQrCodeReader() {
    var lastResult;

    // Hide start button
    document.getElementById('start-button').remove()

    var html5QrcodeScanner = new Html5QrcodeScanner(
        "qr-reader", {
            fps: 10, rememberLastUsedCamera: true, qrbox: qrboxSizeFunction,
            showTorchButtonIfSupported: true
        });
    html5QrcodeScanner.render(onScanSuccess)

    function onScanSuccess(decodedText, decodedResult) {
        if (decodedText !== lastResult) {
            lastResult = decodedText;
            console.log(`Scan result = ${decodedText}`, decodedResult);

            processQrCode(decodedText).then(function (valid) {
                if (valid) {
                    // Clear QR Code Scanner
                    html5QrcodeScanner.clear();

                    // Show top button
                    document.getElementById('stop-card').style.visibility = 'visible';
                    document.getElementById('scan-card').remove();

                } else {
                    lastResult = null;
                }
            });
        }
    }
}

function stopSession() {
    // Call stop session on backend
    stopSessionOnBackend().then(function (success) {
        if (success) {
            // Remove stop card
            document.getElementById('stop-card').remove()

            // Move to profile page
             window.location.href = window.location.origin + "/profile"
        }
        else
            console.log("Something went wrong");
    });
}

document.querySelectorAll('.navbar-link').forEach(function(navbarLink){
  navbarLink.addEventListener('click', function(){
    navbarLink.nextElementSibling.classList.toggle('is-hidden-mobile');
  })
});