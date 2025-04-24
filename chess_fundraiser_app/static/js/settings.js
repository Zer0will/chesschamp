document.addEventListener('DOMContentLoaded', function() {
    let selectedDifficulty = null;
    let selectedColor = null;
    const startButton = document.querySelector('.start-game-button');
    const statusMessage = document.getElementById('status-message');
    
    // Disable start button until selections are made
    updateStartButton();
    
    // Set up difficulty buttons
    const difficultyButtons = document.querySelectorAll('.difficulty-button');
    difficultyButtons.forEach(button => {
        button.addEventListener('click', function() {
            // Remove selected class from all difficulty buttons
            difficultyButtons.forEach(btn => btn.classList.remove('selected'));
            
            // Add selected class to clicked button
            this.classList.add('selected');
            
            // Store the difficulty value
            selectedDifficulty = this.getAttribute('data-value');
            console.log(`Selected difficulty: ${selectedDifficulty}`);
            
            // Update start button state
            updateStartButton();
        });
    });
    
    // Set up color buttons
    const colorButtons = document.querySelectorAll('.color-button');
    colorButtons.forEach(button => {
        button.addEventListener('click', function() {
            // Remove selected class from all color buttons
            colorButtons.forEach(btn => btn.classList.remove('selected'));
            
            // Add selected class to clicked button
            this.classList.add('selected');
            
            // Store the color value
            selectedColor = this.getAttribute('data-value');
            console.log(`Selected color: ${selectedColor}`);
            
            // Update start button state
            updateStartButton();
        });
    });
    
    // Setup start game button
    startButton.addEventListener('click', function() {
        if (selectedDifficulty !== null && selectedColor !== null) {
            // Show loading state
            startButton.disabled = true;
            startButton.textContent = 'Starting Game...';
            statusMessage.textContent = 'Launching chess game...';
            statusMessage.style.color = '#4285f4'; // Blue color for info
            
            // Fetch to start the game
            fetch(`/start-game?difficulty=${selectedDifficulty}&color=${selectedColor}`)
                .then(response => response.json())
                .then(data => {
                    console.log('Game start response:', data);
                    if (data.status === 'success') {
                        // Game launched successfully
                        statusMessage.textContent = data.message;
                        statusMessage.style.color = '#0f9d58'; // Green for success
                        
                        // After a successful launch, keep the UI updated
                        setTimeout(() => {
                            statusMessage.textContent = 'Game is now running. You can close this window.';
                        }, 2000);
                    } else {
                        // Error starting game
                        startButton.disabled = false;
                        startButton.textContent = 'Start Playing';
                        statusMessage.textContent = data.message || 'Error starting game';
                        statusMessage.style.color = '#db4437'; // Red for error
                    }
                })
                .catch(error => {
                    console.error('Error starting game:', error);
                    startButton.disabled = false;
                    startButton.textContent = 'Start Playing';
                    statusMessage.textContent = 'Error starting game. Please try again.';
                    statusMessage.style.color = '#db4437'; // Red for error
                });
        }
    });
    
    // Function to update start button state
    function updateStartButton() {
        if (selectedDifficulty !== null && selectedColor !== null) {
            startButton.classList.add('active');
            startButton.disabled = false;
        } else {
            startButton.classList.remove('active');
            startButton.disabled = true;
        }
    }
}); 