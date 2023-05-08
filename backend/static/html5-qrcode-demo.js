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
    let valid = await fetch( window.location.origin + "/scan_bin", {
                method: "POST",
                body: JSON.stringify({
                    qrcode: `${qrcode}`,
                }),
                headers: {
                    "Content-type": "application/json; charset=UTF-8"
                }
            }).then((response) => response.json())
                .then(function(json){
                    // Print result to screen
                    return json.valid;
                });

    // If the result is valid, clear QR code reader, show notification and redirect
    console.log("Before");
    if (valid) {
        // Close the QR code scanning after result is found
        Bulma().alert({
            type: 'success',
            title: 'QR Code Scanned',
            body: 'QR Code for bin 1234 successfully scanned, you may place containers in bin.',
            confirm: 'OK'
        });
    }
    else {
        // Otherwise, show invalid notification
        Bulma().alert({
            type: 'error',
            title: 'QR Code',
            body: 'The scanned QR code is invalid, please re-scan',
            confirm: 'OK'
        });
    }
    console.log("After 1");

    while (document.getElementsByClassName('modal-card').length !== 0) {
           await new Promise(r => setTimeout(r, 200));
    }

    console.log("After 2");

    return valid;
}

function loadQrCodeReader() {
    var lastResult;

    // Hide start button
    document.getElementById('start-button').remove()

    var html5QrcodeScanner = new Html5QrcodeScanner(
        "qr-reader", {
            fps: 10, qrbox: 250, rememberLastUsedCamera: true,
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

                    // Navigate to container disposal page
                    window.location.href = window.location.origin + "/profile"
                } else {
                    lastResult = null;
                }
            });
        }
    }
}

document.querySelectorAll('.navbar-link').forEach(function(navbarLink){
  navbarLink.addEventListener('click', function(){
    navbarLink.nextElementSibling.classList.toggle('is-hidden-mobile');
  })
});