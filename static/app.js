var column_sort_toggle = false;
var previous_column_sort;
var current_tab = null;


function sortTable(event, element, colNo) {
    var data_table = event.target.closest("table").querySelector("tbody");
    column_sort_toggle = previous_column_sort === colNo ? !column_sort_toggle : false;
    previous_column_sort = colNo;

    var analysis_table_data = Array.from(data_table.children);

    if (element.getAttribute("value") === "string") {
        var sorted = analysis_table_data.sort((a, b) => a.children[colNo].innerText.toLowerCase() > b.children[colNo].innerText.toLowerCase());
    } else if (element.getAttribute("value") === "number") {
        var sorted = analysis_table_data.sort((a, b) => Number(a.children[colNo].innerText) > Number(b.children[colNo].innerText));
    } else if (element.getAttribute("value") === "check") {
        var sorted = analysis_table_data.sort((a, b) => a.children[colNo].firstChild.checked >= b.children[colNo].firstChild.checked);
    } else {
        return;
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
    current_tab = element;
    
    var mySiblings = Array.from(element.parentNode.children);
    var myIndex = mySiblings.indexOf(element);
    var nextSubAreas = Array.from(element.parentNode.nextElementSibling.children);
    
    mySiblings.forEach(sibl => sibl.classList.remove("active"));
    nextSubAreas.forEach(area => area.classList.add("hide"));
    
    nextSubAreas[myIndex].classList.remove("hide");
    element.classList.add("active");

    if(element.classList.contains("title-button")) {
        var titles = Array.from(document.getElementsByClassName("analysis-title"));
        titles.forEach(titl => titl.classList.add("hide"));
        titles[myIndex].classList.remove("hide");
    }
}

function switchTabs(event) {
    event.stopPropagation();

    if(!current_tab) {
        current_tab = document.getElementsByClassName("tab-button active")[0];
    }

    var leftTab = current_tab.previousElementSibling;
    var rightTab = current_tab.nextElementSibling;
    
    if(event.key == "ArrowLeft" && leftTab) {
        return leftTab.click();
    } else if(event.key == "ArrowRight" && rightTab) {
        return rightTab.click();
    }
}

function getSelectedBoxes() {
    return Array.from(document.getElementsByClassName("compare-check")).filter(box => box.checked);
}

function selectMultiAlbums(event) {
    var compareButton = document.getElementById("compare-btn");
    var boxes = getSelectedBoxes();

    if(boxes.length == 0) {
        compareButton.classList.add("hide");
    } else {
        compareButton.classList.remove("hide");
    }

}

function submitMultiAlbums(event) {
    var boxes = getSelectedBoxes();

    if (boxes.length > 5) {
        alert("Too many boxes selected... Max number of selections is: 5");
    } else if (boxes.length == 0) {
        return;
    } else {
        var selectedIds = boxes.map(box => box.value);
        event.target.parentElement.href += selectedIds.join(",");
    }

}

function openChartInNewTab(event) {
    var chart = event.target.previousElementSibling;
    var win = window.open();
    win.document.write(chart.outerHTML);
}

function fileDrag(event) {
    event.preventDefault();
}

function fileDrop(event) {
    event.preventDefault();

    var dt = new DataTransfer();
    dt.items.add(event.dataTransfer.files[0]);
    event.target.files = dt.files;
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

Array.from(document.getElementsByClassName("tab-area")).forEach(element => {
    element.addEventListener("keyup", switchTabs);
});

Array.from(document.getElementsByClassName("compare-check")).forEach(element => {
    element.addEventListener("click", selectMultiAlbums);
});

Array.from(document.getElementsByClassName("chart-button")).forEach(element => {
    element.addEventListener("click", openChartInNewTab);
});

document.getElementById("user-form").addEventListener("submit", goToUser);
document.getElementById("country-select").addEventListener("change", setMarket);

try {
    document.getElementById("compare-btn").addEventListener("click", submitMultiAlbums)
} catch(err) {}

try {
    document.getElementById("tracks_file").addEventListener("dragover", fileDrag);
    document.getElementById("tracks_file").addEventListener("drop", fileDrop);
} catch(e) {}


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
