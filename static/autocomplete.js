document.addEventListener('DOMContentLoaded', function() {
    var inputs = document.querySelectorAll('.autocomplete');

    inputs.forEach(function(input) {
        input.addEventListener('input', function() {
            var query = input.value;
            fetch('/autocomplete?query=' + encodeURIComponent(query))
                .then(response => response.json())
                .then(data => {
                    var dataList = input.nextElementSibling;
                    if (!dataList || dataList.tagName.toLowerCase() !== 'datalist') {
                        dataList = document.createElement('datalist');
                        input.parentNode.insertBefore(dataList, input.nextSibling);
                    }
                    dataList.id = input.name + "-list";
                    input.setAttribute("list", dataList.id);

                    dataList.innerHTML = '';
                    data.forEach(function(item) {
                        var option = document.createElement('option');
                        option.value = item;
                        dataList.appendChild(option);
                    });
                });
        });
    });
});
