var column_sort_toggle = false;
var previous_column_sort;


function sortTable(event, element, colNo) {
    var data_table = event.target.closest("table").querySelector("tbody");
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

function expandNavbar(event, element) {
    if(element.firstChild.tagName == "A") {
       return element.firstChild.click();
    } 

    var show = element.nextSibling;

    for(exp of document.getElementsByClassName("menu-expand")) {
        if (show == exp) {
            exp.classList.toggle("hide");
        } else {
            exp.classList.add("hide")
        }
    }
}

function goToUser(event) {
    event.preventDefault();
    userBase = document.getElementById("user-form").action;
    user_search = document.getElementById("user_search").value;
    window.location = userBase + user_search;
}

function populateMarketSelection(markets) {
    var marketDropDown = document.getElementById("country-select");

    markets.forEach(m => {
        var option = document.createElement("option");
        option.setAttribute("value", m["code"]);
        option.text = m["name"];
        marketDropDown.add(option);
    });

    updateSelectedMarket(marketDropDown.children, null);
}

function setMarket(event) {
    var option = event.target;
    var market = option.value;
    var marketIndex = option.selectedIndex;

    document.cookie = "market=" + market + "; SameSite=Strict; Secure; Path=/; Max-Age=3600";
    option.parentNode.classList.add("hide");

    updateSelectedMarket(option.children, marketIndex);
}

function updateSelectedMarket(marketList, newIndex) {
    var oldIndex = sessionStorage.getItem("selectedMarketIndex");
    var cookie = document.cookie;

    if(oldIndex === null && cookie) {
        var currMarket = cookie.split("market=")[1].split(";")[0];
        for(market of marketList) {
            if(market.value === currMarket) {
                oldIndex = market.index;
                break;
            }
        }
    }

    oldIndex = oldIndex !== null  && cookie ? oldIndex : 0;
    newIndex = newIndex !== null ? newIndex : oldIndex;

    sessionStorage.setItem("selectedMarketIndex", newIndex);

    marketList[oldIndex].removeAttribute("selected");
    marketList[newIndex].setAttribute("selected", "");

    var marketTag = document.getElementById("current-country");
    marketTag.innerText = marketList[newIndex].value;
}

function toggleTabs(event, element) {
    var myIndex = Array.from(element.parentNode.children).indexOf(element);
    var tabPages = document.getElementsByClassName("tab-page");
    
    for(page of tabPages) {
        page.classList.add("hide");
    }

    tabPages[myIndex].classList.remove("hide");

    for(btn of document.getElementsByClassName("tab-button")) {
        btn.classList.remove("active");
    }

    element.classList.add("active");
}


document.querySelectorAll("th")
    .forEach((element, columnNo) => {
        element.addEventListener("click", event => sortTable(event, element, columnNo));
    }
);

Array.from(document.getElementsByClassName("menu-item")).forEach(element => {
    element.addEventListener("click", event => expandNavbar(event, element));
  }
);

Array.from(document.getElementsByClassName("tab-button")).forEach(element => {
    element.addEventListener("click", event => toggleTabs(event, element));
  }
);


document.getElementById("user-form").addEventListener("submit", event => goToUser(event));
document.getElementById("country-select").addEventListener("change", event => setMarket(event));

document.addEventListener("DOMContentLoaded", () => {
    markets = sessionStorage.getItem("markets");
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
