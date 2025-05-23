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
    const variantSelect = document.getElementById('variantSelect');
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
    let currentFrameElement = null;
    
    // Get current video ID, variant and fps from the data attributes
    const videoId = currentVideoId || '';
    const variant = currentVariant || 'full_30';
    let fps = parseInt(videoPlayer.getAttribute('data-fps')) || 30;
    let canonicalFps = parseInt(videoPlayer.getAttribute('data-canonical-fps')) || 30;
    
    // Display the detected FPS
    console.log(`Using video FPS: ${fps}, Canonical FPS: ${canonicalFps}`);
    
    // Add event listener for video metadata loaded to verify FPS
    videoPlayer.addEventListener('loadedmetadata', function() {
        // The backend has already detected the FPS, but we can verify it here
        console.log(`Video loaded. Using FPS: ${fps}`);
        
        // Optional: Show FPS in the UI
        if (document.getElementById('fpsDisplay')) {
            document.getElementById('fpsDisplay').textContent = fps;
        }
    });
    
    // Add event listener for timeupdate to highlight current frame
    videoPlayer.addEventListener('timeupdate', function() {
        const currentTime = videoPlayer.currentTime;
        highlightCurrentFrame(currentTime);
    });
    
    // Function to highlight the current frame in the timeline
    function highlightCurrentFrame(currentTime) {
        // Remove existing current-frame highlight
        if (currentFrameElement) {
            currentFrameElement.classList.remove('current-frame');
        }
        
        // Find the closest frame to the current time
        const frames = frameStrip.querySelectorAll('img');
        let closestFrame = null;
        let closestDiff = Infinity;
        
        frames.forEach(img => {
            const time = parseFloat(img.dataset.time);
            const diff = Math.abs(time - currentTime);
            
            if (diff < closestDiff) {
                closestDiff = diff;
                closestFrame = img;
            }
        });
        
        // Highlight the closest frame
        if (closestFrame) {
            closestFrame.classList.add('current-frame');
            currentFrameElement = closestFrame;
            
            // Check if the frame is near the edge of the visible area
            const frameRect = closestFrame.getBoundingClientRect();
            const stripRect = frameStrip.getBoundingClientRect();
            
            // Calculate how close to the edge the frame is (as a percentage of the strip width)
            const leftEdgeDistance = frameRect.left - stripRect.left;
            const rightEdgeDistance = stripRect.right - frameRect.right;
            const stripWidth = stripRect.width;
            
            // If the frame is within 20% of either edge, scroll to center it
            if (leftEdgeDistance < stripWidth * 0.2 || rightEdgeDistance < stripWidth * 0.2) {
                // Only scroll during actual playback, not when seeking
                if (!videoPlayer.paused) {
                    closestFrame.scrollIntoView({ 
                        behavior: 'smooth', 
                        block: 'nearest', 
                        inline: 'center' 
                    });
                }
            }
        }
    }
    
    // Handle variant selection change
    if (variantSelect) {
        variantSelect.addEventListener('change', function() {
            const selectedVariant = this.value;
            if (selectedVariant && selectedVariant !== variant) {
                window.location.href = `/video/${videoId}?variant=${selectedVariant}`;
            }
        });
    }
    
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
        if (!selectedStartFrame || !selectedEndFrame) {
            showStatus('Please set both start and end frames', true);
            return;
        }
        
        if (!eventTypeInput.value.trim()) {
            showStatus('Please enter an event type', true);
            return;
        }
        
        if (currentEditingAnnotation) {
            // We're editing an existing annotation
            currentEditingAnnotation.start = mapVariantToCanonical(selectedStartFrame);
            currentEditingAnnotation.end = mapVariantToCanonical(selectedEndFrame);
            currentEditingAnnotation.type = eventTypeInput.value.trim();
            currentEditingAnnotation.notes = notesInput.value.trim();
            
            // Clear UI components
            clearAnnotationForm();
            
            // Remove existing row
            currentEditingRow.remove();
            
            // Add updated annotation to table
            addAnnotationToTable(currentEditingAnnotation);
            
            // Reset editing state
            exitEditMode();
            
            showStatus(`Annotation updated`);
        } else {
            // We're adding a new annotation
            const newAnnotation = {
                id: Date.now().toString(),  // Simple unique ID
                start: mapVariantToCanonical(selectedStartFrame),
                end: mapVariantToCanonical(selectedEndFrame),
                type: eventTypeInput.value.trim(),
                notes: notesInput.value.trim()
            };
            
            // Add to our annotations array
            annotations.push(newAnnotation);
            
            // Add to the table
            addAnnotationToTable(newAnnotation);
            
            // Clear UI components
            clearAnnotationForm();
            
            showStatus(`Annotation added`);
        }
        
        // Re-sort annotations
        sortAnnotations();
        refreshAnnotationsList();
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
            // Convert variant frames to canonical frames for storage
            const annotation = {
                id: Date.now().toString(), // Simple unique ID based on timestamp
                start: mapVariantToCanonical(selectedStartFrame),
                end: mapVariantToCanonical(selectedEndFrame),
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
                // Remove any existing highlights first
                row.classList.remove('editing');
                
                // Add highlight only to the currently edited annotation
                if (row.dataset.annotationId === currentEditingAnnotation.id.toString()) {
                    row.classList.add('editing');
                    currentEditingRow = row;
                }
            });
        }
    }
    
    // Enter edit mode for an annotation
    function enterEditMode(annotation, row) {
        // Remove highlight from the previously edited row
        if (currentEditingRow) {
            currentEditingRow.classList.remove('editing');
        }
        
        // Store the annotation being edited
        currentEditingAnnotation = annotation;
        currentEditingRow = row;
        
        // Update form title
        if (annotationPanelTitle) {
            annotationPanelTitle.textContent = 'Edit Annotation';
        }
        
        // Map canonical frames to variant frames for display
        const variantStartFrame = mapCanonicalToVariant(parseInt(annotation.start));
        const variantEndFrame = mapCanonicalToVariant(parseInt(annotation.end));
        
        // Fill form with annotation data (using variant frames for display)
        selectedStartFrame = variantStartFrame;
        selectedEndFrame = variantEndFrame;
        startFrameDisplay.textContent = variantStartFrame;
        endFrameDisplay.textContent = variantEndFrame;
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
        
        // Highlight the start and end frames in the timeline
        // Use variant frames here, not canonical frames
        highlightFrameInTimeline(variantStartFrame, 'selected-start');
        highlightFrameInTimeline(variantEndFrame, 'selected-end');
        
        // Optionally, scroll to the annotation form
        document.getElementById('annotationPanel').scrollIntoView({ behavior: 'smooth' });
    }
    
    // Helper function to highlight a frame in the timeline
    function highlightFrameInTimeline(frameNumber, className) {
        // Remove existing highlights of this class
        frameStrip.querySelectorAll('img.' + className).forEach(img => {
            img.classList.remove(className);
        });
        
        // Find the closest frame to the given frame number
        const frameTime = frameNumber / fps;
        const frames = frameStrip.querySelectorAll('img');
        let closestFrame = null;
        let closestDiff = Infinity;
        
        frames.forEach(img => {
            const time = parseFloat(img.dataset.time);
            const diff = Math.abs(time - frameTime);
            
            if (diff < closestDiff) {
                closestDiff = diff;
                closestFrame = img;
            }
        });
        
        // Highlight the closest frame
        if (closestFrame) {
            closestFrame.classList.add(className);
            
            // Store reference if it's a start or end frame
            if (className === 'selected-start') {
                selectedStartElement = closestFrame;
            } else if (className === 'selected-end') {
                selectedEndElement = closestFrame;
            }
            
            // Scroll the frame into view
            closestFrame.scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'center' });
        }
    }
    
    // Exit edit mode
    function exitEditMode() {
        // Reset editing state
        currentEditingAnnotation = null;
        
        // Remove highlight from the row
        if (currentEditingRow) {
            currentEditingRow.classList.remove('editing');
            currentEditingRow = null;
        } else {
            // If currentEditingRow is not set for some reason, remove highlight from all rows
            const rows = annotationsTable.querySelectorAll('tr');
            rows.forEach(row => {
                row.classList.remove('editing');
            });
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
        // Create a new row
        const row = document.createElement('tr');
        
        // Map annotation frames from canonical to current variant for display
        const variantStartFrame = mapCanonicalToVariant(parseInt(annotation.start));
        const variantEndFrame = mapCanonicalToVariant(parseInt(annotation.end));
        
        // Create cells for the row with the mapped frame values
        const startFrameCell = document.createElement('td');
        startFrameCell.textContent = variantStartFrame;
        startFrameCell.dataset.canonicalFrame = annotation.start;
        
        const endFrameCell = document.createElement('td');
        endFrameCell.textContent = variantEndFrame;
        endFrameCell.dataset.canonicalFrame = annotation.end;
        
        const eventTypeCell = document.createElement('td');
        eventTypeCell.textContent = annotation.type;
        
        const notesCell = document.createElement('td');
        notesCell.textContent = annotation.notes;
        
        const actionsCell = document.createElement('td');
        
        // Create edit button
        const editBtn = document.createElement('button');
        editBtn.textContent = 'Edit';
        editBtn.classList.add('edit-btn');
        editBtn.addEventListener('click', function() {
            enterEditMode(annotation, row);
        });
        
        // Create delete button
        const deleteBtn = document.createElement('button');
        deleteBtn.textContent = 'Delete';
        deleteBtn.classList.add('delete-btn');
        deleteBtn.addEventListener('click', function() {
            // Remove from UI
            row.remove();
            
            // Remove from data
            const index = annotations.findIndex(a => a.id === annotation.id);
            if (index !== -1) {
                annotations.splice(index, 1);
            }
            
            showStatus(`Annotation deleted`);
        });
        
        // Add buttons to the actions cell
        actionsCell.appendChild(editBtn);
        actionsCell.appendChild(deleteBtn);
        
        // Add cells to the row
        row.appendChild(startFrameCell);
        row.appendChild(endFrameCell);
        row.appendChild(eventTypeCell);
        row.appendChild(notesCell);
        row.appendChild(actionsCell);
        
        // Add click event to allow seeking to the frame
        row.addEventListener('click', function(e) {
            // Only proceed if the click wasn't on a button
            if (e.target.tagName !== 'BUTTON') {
                // Seek to the start frame time
                const startFrame = parseInt(annotation.start);
                const currentVariantFrame = mapCanonicalToVariant(startFrame);
                const timeInSeconds = currentVariantFrame / fps;
                videoPlayer.currentTime = timeInSeconds;
            }
        });
        
        // Add a hover effect to highlight the frames in the timeline
        row.addEventListener('mouseenter', function() {
            // Highlight the frames in the timeline
            const startFrame = mapCanonicalToVariant(parseInt(annotation.start));
            const endFrame = mapCanonicalToVariant(parseInt(annotation.end));
            
            highlightFrameInTimeline(startFrame, 'highlighted-start');
            highlightFrameInTimeline(endFrame, 'highlighted-end');
            
            row.classList.add('highlighted-row');
        });
        
        row.addEventListener('mouseleave', function() {
            // Remove all highlighted frames
            const frames = frameStrip.querySelectorAll('img');
            frames.forEach(frame => {
                frame.classList.remove('highlighted-start', 'highlighted-end');
            });
            
            row.classList.remove('highlighted-row');
        });
        
        // Add the new row to the table
        annotationsTable.appendChild(row);
    }
    
    // Function to map canonical frame to variant frame
    function mapCanonicalToVariant(canonicalFrame) {
        // Using the formula from the PRD:
        // variant_frame = round(((canon - clipStartCanon) / C_FPS) * V_FPS)
        return Math.round(((canonicalFrame - clipStartFrame) / canonicalFps) * fps);
    }
    
    // Function to map variant frame to canonical frame
    function mapVariantToCanonical(variantFrame) {
        // Using the formula from the PRD:
        // canon = round((variant_frame / V_FPS) * C_FPS) + clipStartCanon
        return Math.round((variantFrame / fps) * canonicalFps) + clipStartFrame;
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