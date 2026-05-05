document.addEventListener('DOMContentLoaded', function () {
    try {
        document.querySelectorAll('form[autocomplete="off"], input[autocomplete="off"]').forEach(function (element) {
            element.setAttribute('autocomplete', 'off');
        });
    } catch (error) {
        console.error('no-autocomplete.js error:', error);
    }
});
