// Sharedo DOCX to HTML Converter - Frontend JavaScript

let currentHtmlContent = null;

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    loadMetrics();
    setInterval(loadMetrics, 30000); // Refresh metrics every 30 seconds
    
    // Setup form handler
    const form = document.getElementById('converterForm');
    if (form) {
        form.addEventListener('submit', handleConversion);
    }
    
    // Setup reset button
    const resetBtn = document.getElementById('resetBtn');
    if (resetBtn) {
        resetBtn.addEventListener('click', resetForm);
    }
    
    // Setup view button
    const viewBtn = document.getElementById('viewBtn');
    if (viewBtn) {
        viewBtn.addEventListener('click', viewHTML);
    }
    
    // Setup download button
    const downloadBtn = document.getElementById('downloadBtn');
    if (downloadBtn) {
        downloadBtn.addEventListener('click', downloadHTML);
    }
    
    // Setup copy button
    const copyBtn = document.getElementById('copyBtn');
    if (copyBtn) {
        copyBtn.addEventListener('click', copyToClipboard);
    }
});

// Handle form submission
async function handleConversion(event) {
    event.preventDefault();
    
    const fileInput = document.getElementById('fileInput');
    const file = fileInput.files[0];
    
    if (!file) {
        alert('Please select a file');
        return;
    }
    
    // Validate file size (10MB max)
    if (file.size > 10 * 1024 * 1024) {
        alert('File size exceeds 10MB limit');
        return;
    }
    
    // Show progress
    document.getElementById('progressSection').style.display = 'block';
    document.getElementById('resultSection').style.display = 'none';
    document.getElementById('convertBtn').disabled = true;
    
    // Create form data
    const formData = new FormData();
    formData.append('file', file);
    
    try {
        // Call API
        const response = await axios.post('/api/v1/convert', formData, {
            headers: {
                'Content-Type': 'multipart/form-data'
            }
        });
        
        // Handle success
        handleConversionSuccess(response.data);
        
    } catch (error) {
        // Handle error
        handleConversionError(error);
    } finally {
        // Hide progress
        document.getElementById('progressSection').style.display = 'none';
        document.getElementById('convertBtn').disabled = false;
    }
}

// Handle successful conversion
function handleConversionSuccess(data) {
    const resultSection = document.getElementById('resultSection');
    const resultAlert = document.getElementById('resultAlert');
    const resultTitle = document.getElementById('resultTitle');
    const resultMessage = document.getElementById('resultMessage');
    const resultDetails = document.getElementById('resultDetails');
    const downloadBtn = document.getElementById('downloadBtn');
    const viewBtn = document.getElementById('viewBtn');
    
    // Store HTML content
    currentHtmlContent = data.html_content;
    
    // Update UI based on confidence score
    if (data.confidence_score >= 90) {
        resultAlert.className = 'alert alert-success';
        resultTitle.textContent = '✅ Conversion Successful!';
    } else if (data.confidence_score >= 70) {
        resultAlert.className = 'alert alert-warning';
        resultTitle.textContent = '⚠️ Conversion Completed with Warnings';
    } else {
        resultAlert.className = 'alert alert-danger';
        resultTitle.textContent = '⚠️ Conversion Needs Review';
    }
    
    // Set message
    resultMessage.textContent = `Confidence Score: ${data.confidence_score}%`;
    
    // Show details
    let detailsHtml = '';
    
    if (data.sharedo_elements) {
        const elements = data.sharedo_elements;
        let elementCount = 0;
        for (const [key, value] of Object.entries(elements)) {
            if (Array.isArray(value)) {
                elementCount += value.length;
            }
        }
        if (elementCount > 0) {
            detailsHtml += `<p><strong>Sharedo Elements Found:</strong> ${elementCount}</p>`;
        }
    }
    
    if (data.warnings && data.warnings.length > 0) {
        detailsHtml += '<p><strong>Warnings:</strong></p><ul>';
        data.warnings.forEach(warning => {
            detailsHtml += `<li>${warning}</li>`;
        });
        detailsHtml += '</ul>';
    }
    
    if (data.issues && data.issues.length > 0) {
        detailsHtml += '<p><strong>Issues:</strong></p><ul>';
        data.issues.forEach(issue => {
            detailsHtml += `<li>${issue}</li>`;
        });
        detailsHtml += '</ul>';
    }
    
    detailsHtml += `<p><small>Processing Time: ${data.processing_time}s | Conversion ID: ${data.conversion_id}</small></p>`;
    
    resultDetails.innerHTML = detailsHtml;
    
    // Show buttons if HTML content is available
    if (currentHtmlContent) {
        downloadBtn.style.display = 'inline-block';
        viewBtn.style.display = 'inline-block';
    }
    
    // Show result section
    resultSection.style.display = 'block';
    
    // Refresh metrics
    loadMetrics();
}

// Handle conversion error
function handleConversionError(error) {
    const resultSection = document.getElementById('resultSection');
    const resultAlert = document.getElementById('resultAlert');
    const resultTitle = document.getElementById('resultTitle');
    const resultMessage = document.getElementById('resultMessage');
    const resultDetails = document.getElementById('resultDetails');
    
    resultAlert.className = 'alert alert-danger';
    resultTitle.textContent = '❌ Conversion Failed';
    
    if (error.response && error.response.data && error.response.data.detail) {
        resultMessage.textContent = error.response.data.detail;
    } else {
        resultMessage.textContent = 'An error occurred during conversion';
    }
    
    resultDetails.innerHTML = '';
    
    // Hide download/view buttons
    document.getElementById('downloadBtn').style.display = 'none';
    document.getElementById('viewBtn').style.display = 'none';
    
    // Show result section
    resultSection.style.display = 'block';
}

// Reset form
function resetForm() {
    document.getElementById('converterForm').reset();
    document.getElementById('resultSection').style.display = 'none';
    currentHtmlContent = null;
}

// View HTML in modal
function viewHTML() {
    if (!currentHtmlContent) return;
    
    // Format HTML for display
    const formatted = formatHTML(currentHtmlContent);
    document.getElementById('htmlCode').textContent = formatted;
    
    // Show modal
    const modal = new bootstrap.Modal(document.getElementById('htmlModal'));
    modal.show();
}

// Download HTML file
function downloadHTML() {
    if (!currentHtmlContent) return;
    
    const blob = new Blob([currentHtmlContent], { type: 'text/html' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'converted_template.html';
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
    document.body.removeChild(a);
}

// Copy HTML to clipboard
async function copyToClipboard() {
    const code = document.getElementById('htmlCode').textContent;
    try {
        await navigator.clipboard.writeText(code);
        const btn = document.getElementById('copyBtn');
        const originalText = btn.innerHTML;
        btn.innerHTML = '<i class="fas fa-check"></i> Copied!';
        btn.classList.add('btn-success');
        setTimeout(() => {
            btn.innerHTML = originalText;
            btn.classList.remove('btn-success');
        }, 2000);
    } catch (err) {
        alert('Failed to copy to clipboard');
    }
}

// Load and display metrics
async function loadMetrics() {
    try {
        // Load metrics
        const metricsResponse = await axios.get('/metrics');
        const metrics = metricsResponse.data;
        
        // Update metric cards
        document.getElementById('totalConversions').textContent = metrics.total_conversions;
        document.getElementById('successRate').textContent = metrics.success_rate + '%';
        document.getElementById('avgTime').textContent = metrics.average_processing_time + 's';
        
        // Update recent conversions table
        const tbody = document.getElementById('recentConversionsBody');
        if (metrics.recent_conversions && metrics.recent_conversions.length > 0) {
            tbody.innerHTML = '';
            metrics.recent_conversions.reverse().forEach(conversion => {
                const row = document.createElement('tr');
                
                // Format timestamp
                const timestamp = new Date(conversion.timestamp).toLocaleString();
                
                // Status badge
                const statusBadge = conversion.status === 'success' 
                    ? '<span class="badge bg-success">Success</span>'
                    : '<span class="badge bg-danger">Failed</span>';
                
                // Confidence badge
                let confidenceBadge = '-';
                if (conversion.confidence_score !== undefined) {
                    const score = conversion.confidence_score;
                    const badgeClass = score >= 90 ? 'bg-success' : score >= 70 ? 'bg-warning' : 'bg-danger';
                    confidenceBadge = `<span class="badge ${badgeClass}">${score}%</span>`;
                }
                
                row.innerHTML = `
                    <td>${timestamp}</td>
                    <td>${conversion.filename || 'Unknown'}</td>
                    <td>${statusBadge}</td>
                    <td>${confidenceBadge}</td>
                    <td>${conversion.processing_time || '-'}s</td>
                `;
                tbody.appendChild(row);
            });
        } else {
            tbody.innerHTML = '<tr><td colspan="5" class="text-center">No recent conversions</td></tr>';
        }
        
        // Check health status
        const healthResponse = await axios.get('/health');
        if (healthResponse.data.status === 'healthy') {
            document.getElementById('serviceStatus').textContent = 'Online';
            document.getElementById('serviceStatus').className = 'text-success';
        }
        
    } catch (error) {
        console.error('Failed to load metrics:', error);
        document.getElementById('serviceStatus').textContent = 'Offline';
        document.getElementById('serviceStatus').className = 'text-danger';
    }
}

// Format HTML for display
function formatHTML(html) {
    // Basic HTML formatting (indentation)
    let formatted = html;
    let indent = 0;
    
    formatted = formatted.replace(/></g, '>\n<');
    const lines = formatted.split('\n');
    const formattedLines = [];
    
    for (let line of lines) {
        line = line.trim();
        if (line.startsWith('</')) {
            indent = Math.max(0, indent - 1);
        }
        
        formattedLines.push('  '.repeat(indent) + line);
        
        if (line.startsWith('<') && !line.startsWith('</') && !line.includes('/>') && !line.startsWith('<!')) {
            if (!line.includes('</')) {
                indent++;
            }
        }
    }
    
    return formattedLines.join('\n');
}