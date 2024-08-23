document.addEventListener('DOMContentLoaded', function() {
    const codeInput = document.getElementById('code-input');
    const refactoredCode = document.getElementById('refactored-code');
    const loading = document.getElementById('loading');
    const submitButton = document.getElementById('refactor-button');
    const modificationTypeSelect = document.getElementById('modification-type');
    const languageSelect = document.getElementById('language-select');

    let isProcessing = false;

    function generateText() {
        if (isProcessing || codeInput.value.trim() === '') return;

        isProcessing = true;
        
        // Show loading wheel and disable submit button
        loading.classList.add('active');
        submitButton.disabled = true;
        codeInput.disabled = true;

        const modType = modificationTypeSelect.value;
        const language = languageSelect.value;

        fetch('/generate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                prompt: codeInput.value,
                mod_type: modType,
                language: language
            }),
        })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                refactoredCode.innerHTML = `<p style="color: #ff6b6b;">Error: ${data.error}</p>`;
            } else {
                let content = '';
                if (modType === 'lint-improve' || modType === 'pseudo-to-code') {
                    content = `<h3>${modType === 'lint-improve' ? 'Refactored' : 'Generated'} Code:</h3>
                               <pre><code class="language-${language}">${escapeHtml(data.result_code)}</code></pre>
                               <h3>Explanation:</h3>
                               <p>${marked.parse(data.explanation)}</p>`;
                } else {  // abstract
                    content = marked.parse(data.full_response);
                }
                refactoredCode.innerHTML = content;
                refactoredCode.querySelectorAll('pre code').forEach((block) => {
                    hljs.highlightElement(block);
                    addCopyButton(block);
                });
            }
        })
        .catch(error => {
            refactoredCode.innerHTML = `<p style="color: #ff6b6b;">Error: ${error.message}</p>`;
        })
        .finally(() => {
            // Hide loading wheel and enable submit button
            loading.classList.remove('active');
            submitButton.disabled = false;
            codeInput.disabled = false;
            isProcessing = false;
        });
    }

    function addCopyButton(block) {
        const button = document.createElement('button');
        button.textContent = 'Copy';
        button.className = 'copy-button';
        button.addEventListener('click', function() {
            const code = block.textContent;
            navigator.clipboard.writeText(code).then(function() {
                button.textContent = 'Copied!';
                setTimeout(function() {
                    button.textContent = 'Copy';
                }, 2000);
            }, function(err) {
                console.error('Could not copy text: ', err);
            });
        });
        const pre = block.parentNode;
        pre.style.position = 'relative';
        pre.insertBefore(button, block);
    }

    function escapeHtml(unsafe) {
        return unsafe
             .replace(/&/g, "&amp;")
             .replace(/</g, "&lt;")
             .replace(/>/g, "&gt;")
             .replace(/"/g, "&quot;")
             .replace(/'/g, "&#039;");
    }

    // Event listeners
    submitButton.addEventListener('click', generateText);

    // Configure marked to use highlight.js for code highlighting
    marked.setOptions({
        highlight: function(code, lang) {
            const language = hljs.getLanguage(lang) ? lang : 'plaintext';
            return hljs.highlight(code, { language }).value;
        },
        langPrefix: 'hljs language-'
    });
});