var column_sort_toggle = false;
var previous_column_sort;
var current_tab = null;


function sortTable(event) {
    var element = event.target;
    var table = event.target.closest("table");
    var headers = Array.from(table.querySelectorAll("th"))
    var data_table = table.querySelector("tbody");
    var colNo = headers.indexOf(element);
    var sortType = element.dataset.type;

    column_sort_toggle = previous_column_sort === colNo ? !column_sort_toggle : false;
    previous_column_sort = colNo;

    var analysis_table_data = Array.from(data_table.children);

    if (sortType === "string") {
        var sorted = analysis_table_data.sort((a, b) => a.children[colNo].innerText.toLowerCase() > b.children[colNo].innerText.toLowerCase());
    } else if (sortType === "number") {
        var sorted = analysis_table_data.sort((a, b) => Number(a.children[colNo].innerText) > Number(b.children[colNo].innerText));
    } else if (sortType === "check") {
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

function setMarket(event) {
    var option = event.target;
    var market = option.value;
    var marketIndex = option.selectedIndex;

    document.cookie = "market=" + market + "; SameSite=Strict; Secure; Path=/; Max-Age=3600";
    option.parentNode.classList.add("hide");

    updateSelectedMarket(marketIndex);
}

function updateSelectedMarket(newIndex) {
    var oldIndex = sessionStorage.getItem("selectedMarketIndex");
    var cookie = document.cookie;
    var marketList = document.getElementById("country-select").children;

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

function getButtonAndSelectedBoxes(event) {
    var table = event.target.closest("table");
    var compareButton = table.querySelector(".compare-button");
    var boxes = table.querySelectorAll(".compare-check");

    return [compareButton, Array.from(boxes).filter(box => box.checked)];
}

function selectMultiAlbums(event) {
    var [compareButton, boxes] = getButtonAndSelectedBoxes(event);

    if(boxes.length == 0) {
        compareButton.classList.add("hide");
    } else {
        compareButton.classList.remove("hide");
    }
}

function submitMultiAlbums(event) {
    event.preventDefault();
    var [compareButton, boxes] = getButtonAndSelectedBoxes(event);
    var typeLimit = compareButton.dataset.limit;

    if (boxes.length > typeLimit) {
        alert("Too many boxes selected... Max number of selections is: " + typeLimit);
    } else if (boxes.length == 0) {
        return;
    } else {
        var selectedIds = boxes.map(box => box.dataset.value);
        window.location = compareButton.href + selectedIds.join(",")
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


document.querySelectorAll("th").forEach(element => {
    element.addEventListener("click", sortTable);
});

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

Array.from(document.getElementsByClassName("compare-button")).forEach(element => {
    element.addEventListener("click", submitMultiAlbums);
});

document.getElementById("user-form").addEventListener("submit", goToUser);
document.getElementById("country-select").addEventListener("change", setMarket);

try {
    document.getElementById("tracks_file").addEventListener("dragover", fileDrag);
    document.getElementById("tracks_file").addEventListener("drop", fileDrop);
} catch(e) {}


document.addEventListener("DOMContentLoaded", () => {
    updateSelectedMarket(null);
});
