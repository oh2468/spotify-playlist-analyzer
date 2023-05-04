var column_sort_toggle = false;
var previous_column_sort;


function sortTable(event, element, colNo) {
    //var data_table = document.getElementById("analysis-result-table").querySelector("tbody");
    //console.log(event);
    var data_table = event.target.closest("table").querySelector("tbody");
    //console.log(data_table);
    column_sort_toggle = previous_column_sort === colNo ? !column_sort_toggle : false;
    previous_column_sort = colNo;

    var analysis_table_data = Array.from(data_table.children);

    if (element.getAttribute("value") !== "number") {
        var sorted = analysis_table_data.sort((a, b) => a.children[colNo].innerText.toLowerCase() > b.children[colNo].innerText.toLowerCase());
    } else {
        var sorted = analysis_table_data.sort((a, b) => Number(a.children[colNo].innerText) > Number(b.children[colNo].innerText));
    }
    
    sorted = column_sort_toggle ? sorted.reverse() : sorted;

    data_table.innerHTML = "";
    sorted.forEach(e => data_table.append(e));
}

function expandSearch(event, element) {
    //console.log(event);
    //console.log(element);
    var show = element.nextSibling;
    //console.log(show);
    var dis = show.style.display;
    for(exp of document.getElementsByClassName("menu-expand")) {
        exp.style.display = "none"
    }
    show.style.display = dis == "none" ? "" : "none";
}

function goToUser(event) {
    console.log(event);
    console.log(event.target);
}

function populateMarketSelection(markets) {
    var marketDropDown = document.getElementById("country-select");
    markets.forEach(m => {
        var option = document.createElement("option");
        option.setAttribute("value", m["code"]);
        option.text = m["name"];
        marketDropDown.add(option);
    })
}

function setMarket(event) {
    //console.log(event);
    market = event.target.value;
    document.cookie = "market=" + market + "; SameSite=Strict; Secure";
    var marketTag = document.getElementById("current-country");
    marketTag.innerText = market;
    event.target.parentNode.style = "display: None;"
}



document.querySelectorAll("th")
    .forEach((element, columnNo) => {
        element.addEventListener("click", event => sortTable(event, element, columnNo));
    }
);


Array.from(document.getElementsByClassName("menu-item")).forEach(element => {
    element.addEventListener("click", event => expandSearch(event, element));
  }
);

document.getElementById("user-form").addEventListener("submit", event => goToUser(event));
document.getElementById("country-select").addEventListener("change", event => setMarket(event));

document.addEventListener("DOMContentLoaded", () => {
    markets = sessionStorage.getItem("markets")
    if(markets) {
        populateMarketSelection(JSON.parse(markets));
    } else {
        fetch("/markets")
        .then(resp => resp.json())
        .then(markets => {
            sessionStorage.setItem("markets", JSON.stringify(markets));
            populateMarketSelection(markets);
        })
        .catch(err => console.log(err));
    }
});
