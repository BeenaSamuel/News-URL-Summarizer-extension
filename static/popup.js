document.addEventListener("DOMContentLoaded", function () {
  document
    .getElementById("summarizeButton")
    .addEventListener("click", function () {
      chrome.tabs.query({ active: true, currentWindow: true }, function (tabs) {
        // var currentUrl = tabs[0].url;
        // summarizeUrl(currentUrl);
        var currentUrl = tabs[0].url;
        var summaryType = document.querySelector(
          'input[name="flexRadioDefault"]:checked'
        ).value;
        var summaryLength = document.getElementById('customRange2').value;
        // summarizeUrl(currentUrl, summaryType);
        summarizeUrl(currentUrl, summaryType, summaryLength );
      });
    });
});

// function summarizeUrl(url) {
//     // Send message to background script to summarize the URL
//     chrome.runtime.sendMessage({ action: 'summarize', url: url }, function (response) {
//         document.getElementById('summary').innerText = response.summary;
//     });
// }

// function summarizeUrl(url,summaryType, summaryLength ) {
//     // Send message to background script to summarize the URL
//     chrome.runtime.sendMessage({ action: 'summarize_url', url: url, summaryType: summaryType, summaryLength: summaryLength }, function (response) {
//         if (response && response.summary) {
//             document.getElementById('summary').innerText = response.summary;
//             print(response.headline)
//             document.getElementById('headline').innerHTML= response.headline;

//         } else {
//             console.error('Error: Invalid response received from background script');
//             document.getElementById('summary').innerText = 'Error: Unable to retrieve summary';
//         }
//     });
// }

// function summarizeUrl(url, summaryType) {
  function summarizeUrl(url, summaryType, summaryLength) {
  chrome.runtime.sendMessage(
    // { action: "summarize_url", url: url, summaryType: summaryType },
    { action: "summarize_url", url: url, summaryType: summaryType ,summaryLength },
    function (response) {
      if (response && response.summary) {
        var summaryList = document.createElement("ul");
        response.summary.forEach(function (summaryObj) {
          var summaryItem = document.createElement("li");
          summaryItem.innerText = summaryObj.sentence;
          summaryList.appendChild(summaryItem);
        });

        document.getElementById("summary").appendChild(summaryList);
        var percentageReduction = (
          ((parseInt(response.articleWords) - parseInt(response.wordCount)) /
            parseInt(response.articleWords)) *
          100
        ).toFixed(2);
        document.getElementById("headline").innerHTML = response.headline;
        document.getElementById("article-words").innerHTML =
          "Number of words in article " + " " + response.articleWords;
        document.getElementById("words").innerHTML =
          "Number of words in summary " + " " + response.wordCount;
        document.getElementById("reduction-percent").innerHTML =
          "Percentage reduced " + " " + percentageReduction + " %";
        var seperators = document.getElementsByClassName("seperator");
        for (var i = 0; i < seperators.length; i++) {
          seperators[i].innerText =
            "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~";
        }
      } else {
        console.error(
          "Error: Invalid response received from background script"
        );
        document.getElementById("summary").innerText =
          "Error: Unable to retrieve summary";
      }
    }
  );
}
