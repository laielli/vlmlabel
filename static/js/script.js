document.addEventListener('DOMContentLoaded', function() {
    // DOM elements
    const videoPlayer = document.getElementById('videoPlayer');
    const frameStrip = document.getElementById('frameStrip');
    const setStartBtn = document.getElementById('setStartBtn');
    const setEndBtn = document.getElementById('setEndBtn');
    const startFrameDisplay = document.getElementById('startFrameDisplay');
    const endFrameDisplay = document.getElementById('endFrameDisplay');
    const eventTypeInput = document.getElementById('eventTypeInput');
    const notesInput = document.getElementById('notesInput');
    const addAnnotationBtn = document.getElementById('addAnnotationBtn');
    const annotationsTable = document.getElementById('annotationsTable').querySelector('tbody');
    const saveBtn = document.getElementById('saveBtn');
    const csvFileInput = document.getElementById('csvFileInput');
    const statusMessage = document.getElementById('statusMessage');
    const videoSelect = document.getElementById('videoSelect');
    const annotationPanelTitle = document.getElementById('annotationPanelTitle');
    const cancelEditBtn = document.getElementById('cancelEditBtn');
    const saveAsNewBtn = document.getElementById('saveAsNewBtn');
    
    // State variables
    let annotations = [];
    let selectedStartFrame = null;
    let selectedEndFrame = null;
    let selectedStartElement = null;
    let selectedEndElement = null;
    let currentEditingAnnotation = null;
    let currentEditingRow = null;
    
    // Get current video ID and fps from the data attributes
    const videoId = currentVideoId || '';
    let fps = parseInt(videoPlayer.getAttribute('data-fps')) || 5;
    
    // Display the detected FPS
    console.log(`Using video FPS: ${fps}`);
    
    // Add event listener for video metadata loaded to verify FPS
    videoPlayer.addEventListener('loadedmetadata', function() {
        // The backend has already detected the FPS, but we can verify it here
        console.log(`Video loaded. Using FPS: ${fps}`);
        
        // Optional: Show FPS in the UI
        if (document.getElementById('fpsDisplay')) {
            document.getElementById('fpsDisplay').textContent = fps;
        }
    });
    
    // Initialize with any existing annotations
    if (typeof initialAnnotations !== 'undefined' && initialAnnotations.length > 0) {
        annotations = initialAnnotations;
        
        // Sort annotations before adding to the table
        sortAnnotations();
        
        // Add existing annotations to the table
        annotations.forEach(annotation => {
            addAnnotationToTable(annotation);
        });
        
        showStatus(`Loaded ${annotations.length} annotations`);
    }
    
    // Handle video selection change
    if (videoSelect) {
        videoSelect.addEventListener('change', function() {
            const selectedVideoId = this.value;
            if (selectedVideoId && selectedVideoId !== videoId) {
                // Check if there are unsaved annotations
                if (annotations.length > 0) {
                    const confirmed = confirm('You have unsaved annotations. Do you want to switch videos? Your current annotations will be lost.');
                    if (!confirmed) {
                        // Reset the dropdown to the current video
                        videoSelect.value = videoId;
                        return;
                    }
                }
                // Navigate to the selected video
                window.location.href = `/video/${selectedVideoId}`;
            }
        });
    }
    
    // Event handling for frame thumbnails
    frameStrip.querySelectorAll('img').forEach(img => {
        img.addEventListener('click', function() {
            const time = parseFloat(this.dataset.time);
            // Ensure the time is valid and set it
            if (!isNaN(time) && time >= 0) {
                // Force the video to seek to the exact time
                videoPlayer.pause();
                videoPlayer.currentTime = time;
                // Optional: Play the video after a small delay to ensure the seek completes
                // setTimeout(() => {
                //     videoPlayer.play().catch(e => {
                //         // Handle any autoplay restrictions
                //         console.log("Could not automatically play after seeking:", e);
                //     });
                // }, 50);
            }
        });
    });
    
    // Set start frame
    setStartBtn.addEventListener('click', function() {
        // Get the current frame based on video time
        const currentTime = videoPlayer.currentTime;
        const frameNumber = Math.round(currentTime * fps);
        
        // Update UI
        if (selectedStartElement) {
            selectedStartElement.classList.remove('selected-start');
        }
        
        // Find the closest frame thumbnail and highlight it
        const closestFrame = findClosestFrameThumbnail(currentTime);
        if (closestFrame) {
            closestFrame.classList.add('selected-start');
            selectedStartElement = closestFrame;
        }
        
        // Update state
        selectedStartFrame = frameNumber;
        startFrameDisplay.textContent = frameNumber;
        
        // Check if we can enable the Add button
        checkEnableAddButton();
    });
    
    // Set end frame
    setEndBtn.addEventListener('click', function() {
        // Get the current frame based on video time
        const currentTime = videoPlayer.currentTime;
        const frameNumber = Math.round(currentTime * fps);
        
        // Update UI
        if (selectedEndElement) {
            selectedEndElement.classList.remove('selected-end');
        }
        
        // Find the closest frame thumbnail and highlight it
        const closestFrame = findClosestFrameThumbnail(currentTime);
        if (closestFrame) {
            closestFrame.classList.add('selected-end');
            selectedEndElement = closestFrame;
        }
        
        // Update state
        selectedEndFrame = frameNumber;
        endFrameDisplay.textContent = frameNumber;
        
        // Check if we can enable the Add button
        checkEnableAddButton();
    });
    
    // Add or update annotation
    addAnnotationBtn.addEventListener('click', function() {
        const eventType = eventTypeInput.value.trim();
        const notes = notesInput.value.trim();
        
        if (!eventType) {
            showStatus('Event Type is required', true);
            return;
        }
        
        if (currentEditingAnnotation) {
            // Update existing annotation
            currentEditingAnnotation.start = selectedStartFrame;
            currentEditingAnnotation.end = selectedEndFrame;
            currentEditingAnnotation.type = eventType;
            currentEditingAnnotation.notes = notes;
            
            // Remove the old row
            if (currentEditingRow) {
                currentEditingRow.remove();
            }
            
            // Add updated row
            addAnnotationToTable(currentEditingAnnotation);
            
            // Resort annotations
            sortAnnotations();
            refreshAnnotationsList();
            
            showStatus('Annotation updated');
            
            // Clear form but stay in edit mode
            exitEditMode();
        } else {
            // Create new annotation object
            const annotation = {
                id: Date.now(), // Simple unique ID based on timestamp
                start: selectedStartFrame,
                end: selectedEndFrame,
                type: eventType,
                notes: notes
            };
            
            // Add to annotations array
            annotations.push(annotation);
            
            // Sort annotations
            sortAnnotations();
            
            // Refresh the list
            refreshAnnotationsList();
            
            // Clear form
            clearAnnotationForm();
            
            showStatus('Annotation added');
        }
    });
    
    // Save as new annotation
    if (saveAsNewBtn) {
        saveAsNewBtn.addEventListener('click', function() {
            const eventType = eventTypeInput.value.trim();
            const notes = notesInput.value.trim();
            
            if (!eventType) {
                showStatus('Event Type is required', true);
                return;
            }
            
            // Create new annotation object
            const annotation = {
                id: Date.now(), // Simple unique ID based on timestamp
                start: selectedStartFrame,
                end: selectedEndFrame,
                type: eventType,
                notes: notes
            };
            
            // Add to annotations array
            annotations.push(annotation);
            
            // Sort annotations
            sortAnnotations();
            
            // Refresh the list
            refreshAnnotationsList();
            
            // Exit edit mode
            exitEditMode();
            
            showStatus('New annotation created');
        });
    }
    
    // Cancel editing
    if (cancelEditBtn) {
        cancelEditBtn.addEventListener('click', function() {
            exitEditMode();
        });
    }
    
    // Save annotations to CSV
    saveBtn.addEventListener('click', function() {
        if (annotations.length === 0) {
            showStatus('No annotations to save', true);
            return;
        }
        
        // Send data to server
        fetch(`/save_annotations/${videoId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ annotations: annotations }),
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                showStatus(`Annotations saved successfully as ${data.filename}`);
            } else {
                showStatus('Error: ' + data.message, true);
            }
        })
        .catch(error => {
            showStatus('Error saving annotations: ' + error.message, true);
        });
    });
    
    // Load CSV file
    csvFileInput.addEventListener('change', function(e) {
        const file = e.target.files[0];
        if (!file) return;
        
        const formData = new FormData();
        formData.append('file', file);
        
        fetch(`/load_annotations/${videoId}`, {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                // Clear existing annotations
                annotations = [];
                annotationsTable.innerHTML = '';
                
                // Add loaded annotations and assign IDs if they don't have them
                data.annotations.forEach(annotation => {
                    if (!annotation.id) {
                        annotation.id = Date.now() + Math.random();
                    }
                    annotations.push(annotation);
                });
                
                // Sort annotations
                sortAnnotations();
                
                // Refresh the list
                refreshAnnotationsList();
                
                showStatus(`Loaded ${data.annotations.length} annotations from ${data.filename}`);
            } else {
                showStatus('Error: ' + data.message, true);
            }
        })
        .catch(error => {
            showStatus('Error loading annotations: ' + error.message, true);
        });

        // Reset file input value to allow loading the same file again
        this.value = '';
    });
    
    // Helper functions
    
    // Sort annotations by start frame (ascending) and duration (descending)
    function sortAnnotations() {
        annotations.sort((a, b) => {
            // First sort by start frame (ascending)
            const startFrameComparison = a.start - b.start;
            
            // If start frames are the same, sort by duration (descending)
            if (startFrameComparison === 0) {
                const durationA = a.end - a.start;
                const durationB = b.end - b.start;
                return durationB - durationA; // Descending order
            }
            
            return startFrameComparison;
        });
    }
    
    // Refresh the annotations list in the UI
    function refreshAnnotationsList() {
        // Clear the table
        annotationsTable.innerHTML = '';
        
        // Add all annotations in sorted order
        annotations.forEach(annotation => {
            addAnnotationToTable(annotation);
        });
        
        // If we were editing an annotation, highlight it again
        if (currentEditingAnnotation) {
            const rows = annotationsTable.querySelectorAll('tr');
            rows.forEach(row => {
                if (row.dataset.annotationId === currentEditingAnnotation.id.toString()) {
                    row.classList.add('editing');
                    currentEditingRow = row;
                }
            });
        }
    }
    
    // Enter edit mode for an annotation
    function enterEditMode(annotation, row) {
        // Store the annotation being edited
        currentEditingAnnotation = annotation;
        currentEditingRow = row;
        
        // Update form title
        if (annotationPanelTitle) {
            annotationPanelTitle.textContent = 'Edit Annotation';
        }
        
        // Fill form with annotation data
        selectedStartFrame = annotation.start;
        selectedEndFrame = annotation.end;
        startFrameDisplay.textContent = annotation.start;
        endFrameDisplay.textContent = annotation.end;
        eventTypeInput.value = annotation.type;
        notesInput.value = annotation.notes;
        
        // Enable the add/update button
        addAnnotationBtn.disabled = false;
        
        // Show edit mode buttons
        if (cancelEditBtn) cancelEditBtn.style.display = 'inline-block';
        if (saveAsNewBtn) saveAsNewBtn.style.display = 'inline-block';
        
        // Change primary button text
        addAnnotationBtn.textContent = 'Update Annotation';
        
        // Highlight the row being edited
        row.classList.add('editing');
        
        // Optionally, scroll to the annotation form
        document.getElementById('annotationPanel').scrollIntoView({ behavior: 'smooth' });
    }
    
    // Exit edit mode
    function exitEditMode() {
        // Reset editing state
        currentEditingAnnotation = null;
        
        // Remove highlight from the row
        if (currentEditingRow) {
            currentEditingRow.classList.remove('editing');
            currentEditingRow = null;
        }
        
        // Update form title
        if (annotationPanelTitle) {
            annotationPanelTitle.textContent = 'Create Annotation';
        }
        
        // Reset form
        clearAnnotationForm();
        
        // Hide edit mode buttons
        if (cancelEditBtn) cancelEditBtn.style.display = 'none';
        if (saveAsNewBtn) saveAsNewBtn.style.display = 'none';
        
        // Change primary button text back
        addAnnotationBtn.textContent = 'Add Annotation';
    }
    
    // Find the closest frame thumbnail to a given time
    function findClosestFrameThumbnail(time) {
        let closestFrame = null;
        let closestDiff = Infinity;
        
        frameStrip.querySelectorAll('img').forEach(img => {
            const frameTime = parseFloat(img.dataset.time);
            const diff = Math.abs(frameTime - time);
            
            if (diff < closestDiff) {
                closestDiff = diff;
                closestFrame = img;
            }
        });
        
        return closestFrame;
    }
    
    // Check if Add button should be enabled
    function checkEnableAddButton() {
        if (selectedStartFrame !== null && selectedEndFrame !== null) {
            addAnnotationBtn.disabled = false;
        } else {
            addAnnotationBtn.disabled = true;
        }
    }
    
    // Clear annotation form
    function clearAnnotationForm() {
        selectedStartFrame = null;
        selectedEndFrame = null;
        eventTypeInput.value = '';
        notesInput.value = '';
        startFrameDisplay.textContent = '---';
        endFrameDisplay.textContent = '---';
        
        if (selectedStartElement) {
            selectedStartElement.classList.remove('selected-start');
            selectedStartElement = null;
        }
        
        if (selectedEndElement) {
            selectedEndElement.classList.remove('selected-end');
            selectedEndElement = null;
        }
        
        addAnnotationBtn.disabled = true;
    }
    
    // Add annotation to the table
    function addAnnotationToTable(annotation) {
        const row = document.createElement('tr');
        
        // Add annotation ID as data attribute for easy reference
        if (annotation.id) {
            row.dataset.annotationId = annotation.id;
        }
        
        // Create cells for each property
        const startCell = document.createElement('td');
        const startFrame = annotation.start;
        const startTime = (startFrame / fps).toFixed(2);
        startCell.innerHTML = `${startFrame} <span class="timestamp">(${startTime}s)</span>`;
        row.appendChild(startCell);
        
        const endCell = document.createElement('td');
        const endFrame = annotation.end;
        const endTime = (endFrame / fps).toFixed(2);
        endCell.innerHTML = `${endFrame} <span class="timestamp">(${endTime}s)</span>`;
        row.appendChild(endCell);
        
        const typeCell = document.createElement('td');
        typeCell.textContent = annotation.type;
        row.appendChild(typeCell);
        
        const notesCell = document.createElement('td');
        notesCell.textContent = annotation.notes;
        row.appendChild(notesCell);
        
        // Add delete button
        const actionCell = document.createElement('td');
        const deleteBtn = document.createElement('button');
        deleteBtn.textContent = '✕';
        deleteBtn.classList.add('delete-btn');
        deleteBtn.addEventListener('click', function(e) {
            e.stopPropagation(); // Prevent row click
            
            // Remove from array
            const index = annotations.findIndex(a => 
                (a.id && a.id === annotation.id) || 
                (a.start === annotation.start && 
                a.end === annotation.end && 
                a.type === annotation.type)
            );
            
            if (index !== -1) {
                annotations.splice(index, 1);
            }
            
            // Remove from table
            row.remove();
            
            // If this was the annotation being edited, exit edit mode
            if (currentEditingAnnotation && 
                ((currentEditingAnnotation.id && currentEditingAnnotation.id === annotation.id) || 
                 (currentEditingAnnotation.start === annotation.start && 
                  currentEditingAnnotation.end === annotation.end && 
                  currentEditingAnnotation.type === annotation.type))) {
                exitEditMode();
            }
            
            showStatus('Annotation deleted');
        });
        
        actionCell.appendChild(deleteBtn);
        row.appendChild(actionCell);
        
        // Add row to table
        annotationsTable.appendChild(row);
        
        // Add click event for editing and jumping to time
        row.addEventListener('click', function(e) {
            // Don't trigger if clicking the delete button
            if (e.target.classList.contains('delete-btn')) return;
            
            // Load annotation for editing
            enterEditMode(annotation, row);
            
            // Find the start frame and jump to it
            const frameTime = annotation.start / fps;
            videoPlayer.currentTime = frameTime;
        });
    }
    
    // Show status message
    function showStatus(message, isError = false) {
        statusMessage.textContent = message;
        
        if (isError) {
            statusMessage.classList.add('error');
        } else {
            statusMessage.classList.remove('error');
        }
        
        // Show the message
        statusMessage.style.display = 'block';
        
        // Hide after 3 seconds
        setTimeout(() => {
            statusMessage.style.display = 'none';
        }, 3000);
    }
}); 