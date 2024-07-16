chrome.runtime.onMessage.addListener(function (request, sender, sendResponse) {
    if (request.action === 'summarize_url') {
        var url = request.url;
        var summaryType = request.summaryType;
        var summaryLength = request.summaryLength;
       
        fetch('http://localhost:5000/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            // body: JSON.stringify({ url: url , summaryType: summaryType })
            body: JSON.stringify({ url: url , summaryType: summaryType , summaryLength : summaryLength})
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
       
        .then(data => {
            sendResponse({ summary: data.summary, headline: data.headline , wordCount : data.wordCount , articleWords : data.articleWords});
            
        })
        .catch(error => {
            console.error('Error fetching data:', error);
            sendResponse({ error: error.message });
        });
        return true; 
    }
});
