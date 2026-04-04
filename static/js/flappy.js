// ========================================
// FLAPPY BIRD GAME - SIMPLIFIED
// ========================================

class FlappyBirdGame {
    constructor(canvasId) {
        console.log('FlappyBirdGame constructor called with:', canvasId);
        
        this.canvas = document.getElementById(canvasId);
        if (!this.canvas) {
            console.error('Canvas element not found:', canvasId);
            return;
        }
        
        console.log('Canvas found:', this.canvas);
        this.ctx = this.canvas.getContext('2d');
        
        this.isRunning = false;
        this.animationId = null;
        
        this.reset();
        this.bindEvents();
        
        console.log('Game initialized, ready to start');
    }

    reset() {
        this.bird = {
            x: 150,
            y: this.canvas.height / 2,
            radius: 20,
            velocity: 0,
            gravity: 0.5,
            jumpPower: -9,
            rotation: 0
        };

        this.pipes = [];
        this.score = 0;
        this.isGameOver = false;
        this.pipeGap = 180;
        this.pipeWidth = 80;
        this.pipeSpeed = 3;
        this.frameCount = 0;
        this.groundX = 0;
        
        console.log('Game reset complete');
    }

    bindEvents() {
        // Remove old listeners if they exist
        if (this.keyHandler) {
            document.removeEventListener('keydown', this.keyHandler);
        }
        if (this.clickHandler) {
            this.canvas.removeEventListener('click', this.clickHandler);
        }
        
        // Create bound handlers
        this.keyHandler = (e) => {
            if (e.key === ' ' || e.key === 'Spacebar') {
                e.preventDefault();
                this.handleJump();
            }
        };
        
        this.clickHandler = (e) => {
            e.preventDefault();
            this.handleJump();
        };
        
        document.addEventListener('keydown', this.keyHandler);
        this.canvas.addEventListener('click', this.clickHandler);
        
        console.log('Event listeners bound');
    }
    
    handleJump() {
        if (this.isGameOver) {
            console.log('Restarting game...');
            this.restart();
        } else if (this.isRunning) {
            this.bird.velocity = this.bird.jumpPower;
        }
    }

    update() {
        if (this.isGameOver || !this.isRunning) return;

        // Update bird physics
        this.bird.velocity += this.bird.gravity;
        this.bird.y += this.bird.velocity;

        // Update bird rotation
        this.bird.rotation = Math.min(Math.max(this.bird.velocity * 3, -30), 90);

        // Generate pipes
        if (this.frameCount % 90 === 0) {
            const minY = 80;
            const maxY = this.canvas.height - this.pipeGap - 130;
            const pipeY = Math.random() * (maxY - minY) + minY;
            
            this.pipes.push({
                x: this.canvas.width,
                y: pipeY,
                width: this.pipeWidth,
                height: this.pipeGap,
                passed: false
            });
        }

        // Update pipes
        for (let i = this.pipes.length - 1; i >= 0; i--) {
            const pipe = this.pipes[i];
            pipe.x -= this.pipeSpeed;

            // Check if bird passed pipe
            if (!pipe.passed && pipe.x + pipe.width < this.bird.x - this.bird.radius) {
                pipe.passed = true;
                this.score++;
            }

            // Check collision
            if (this.checkCollision(pipe)) {
                this.gameOver();
            }

            // Remove off-screen pipes
            if (pipe.x + pipe.width < 0) {
                this.pipes.splice(i, 1);
            }
        }

        // Check boundaries
        const groundLevel = this.canvas.height - 50;
        if (this.bird.y - this.bird.radius < 0 || this.bird.y + this.bird.radius > groundLevel) {
            this.gameOver();
        }

        // Update ground
        this.groundX -= this.pipeSpeed;
        if (this.groundX <= -50) {
            this.groundX = 0;
        }

        this.frameCount++;
    }

    checkCollision(pipe) {
        const birdLeft = this.bird.x - this.bird.radius;
        const birdRight = this.bird.x + this.bird.radius;
        const birdTop = this.bird.y - this.bird.radius;
        const birdBottom = this.bird.y + this.bird.radius;

        const pipeLeft = pipe.x;
        const pipeRight = pipe.x + pipe.width;

        if (birdRight > pipeLeft && birdLeft < pipeRight) {
            if (birdTop < pipe.y || birdBottom > pipe.y + pipe.height) {
                return true;
            }
        }
        return false;
    }

    draw() {
        // Sky background
        const gradient = this.ctx.createLinearGradient(0, 0, 0, this.canvas.height);
        gradient.addColorStop(0, '#4EC0CA');
        gradient.addColorStop(1, '#87CEEB');
        this.ctx.fillStyle = gradient;
        this.ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);

        // Draw pipes
        this.pipes.forEach(pipe => {
            this.drawPipe(pipe);
        });

        // Draw ground
        this.drawGround();

        // Draw bird
        this.drawBird();

        // Draw score
        this.ctx.fillStyle = '#fff';
        this.ctx.strokeStyle = '#000';
        this.ctx.lineWidth = 4;
        this.ctx.font = 'bold 48px Arial';
        this.ctx.textAlign = 'center';
        this.ctx.strokeText(this.score, this.canvas.width / 2, 70);
        this.ctx.fillText(this.score, this.canvas.width / 2, 70);

        // Draw start message or game over
        if (!this.isRunning && !this.isGameOver) {
            this.drawStartScreen();
        } else if (this.isGameOver) {
            this.drawGameOver();
        }

        this.ctx.textAlign = 'left';
    }

    drawStartScreen() {
        this.ctx.fillStyle = 'rgba(0, 0, 0, 0.5)';
        this.ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);
        
        this.ctx.fillStyle = '#fff';
        this.ctx.strokeStyle = '#000';
        this.ctx.lineWidth = 4;
        this.ctx.font = 'bold 48px Arial';
        this.ctx.textAlign = 'center';
        this.ctx.strokeText('FLAPPY BIRD', this.canvas.width / 2, this.canvas.height / 2 - 40);
        this.ctx.fillText('FLAPPY BIRD', this.canvas.width / 2, this.canvas.height / 2 - 40);
        
        this.ctx.font = '24px Arial';
        this.ctx.strokeText('Click or Press SPACE to Start', this.canvas.width / 2, this.canvas.height / 2 + 20);
        this.ctx.fillText('Click or Press SPACE to Start', this.canvas.width / 2, this.canvas.height / 2 + 20);
    }

    drawBird() {
        this.ctx.save();
        this.ctx.translate(this.bird.x, this.bird.y);
        this.ctx.rotate((this.bird.rotation * Math.PI) / 180);

        // Bird body
        this.ctx.fillStyle = '#FFD700';
        this.ctx.beginPath();
        this.ctx.arc(0, 0, this.bird.radius, 0, Math.PI * 2);
        this.ctx.fill();

        // Outline
        this.ctx.strokeStyle = '#000';
        this.ctx.lineWidth = 2;
        this.ctx.stroke();

        // Eye white
        this.ctx.fillStyle = '#fff';
        this.ctx.beginPath();
        this.ctx.arc(8, -5, 6, 0, Math.PI * 2);
        this.ctx.fill();

        // Eye pupil
        this.ctx.fillStyle = '#000';
        this.ctx.beginPath();
        this.ctx.arc(10, -5, 3, 0, Math.PI * 2);
        this.ctx.fill();

        // Beak
        this.ctx.fillStyle = '#FFA500';
        this.ctx.beginPath();
        this.ctx.moveTo(15, 0);
        this.ctx.lineTo(25, -3);
        this.ctx.lineTo(25, 3);
        this.ctx.closePath();
        this.ctx.fill();
        this.ctx.stroke();

        this.ctx.restore();
    }

    drawPipe(pipe) {
        const pipeColor = '#2ECC71';
        const pipeDark = '#27AE60';
        const pipeHighlight = '#82E0AA';

        // Top pipe
        this.drawPipeSegment(pipe.x, 0, pipe.width, pipe.y, pipeColor, pipeDark, pipeHighlight);
        
        // Bottom pipe
        this.drawPipeSegment(pipe.x, pipe.y + pipe.height, pipe.width, 
            this.canvas.height - pipe.y - pipe.height - 50, pipeColor, pipeDark, pipeHighlight);
    }

    drawPipeSegment(x, y, width, height, color, dark, highlight) {
        // Main pipe body
        this.ctx.fillStyle = color;
        this.ctx.fillRect(x, y, width, height);

        // Highlight
        this.ctx.fillStyle = highlight;
        this.ctx.fillRect(x + 5, y, 8, height);

        // Dark edge
        this.ctx.fillStyle = dark;
        this.ctx.fillRect(x + width - 5, y, 5, height);

        // Pipe cap
        const capHeight = 30;
        if (y === 0) {
            this.ctx.fillStyle = color;
            this.ctx.fillRect(x - 5, y + height - capHeight, width + 10, capHeight);
            this.ctx.fillStyle = highlight;
            this.ctx.fillRect(x - 3, y + height - capHeight, 8, capHeight);
        } else {
            this.ctx.fillStyle = color;
            this.ctx.fillRect(x - 5, y, width + 10, capHeight);
            this.ctx.fillStyle = highlight;
            this.ctx.fillRect(x - 3, y, 8, capHeight);
        }
    }

    drawGround() {
        const groundHeight = 50;
        const groundY = this.canvas.height - groundHeight;

        // Ground
        this.ctx.fillStyle = '#DEB887';
        this.ctx.fillRect(0, groundY, this.canvas.width, groundHeight);

        // Grass pattern
        this.ctx.fillStyle = '#2ECC71';
        for (let i = this.groundX; i < this.canvas.width; i += 50) {
            this.ctx.fillRect(i, groundY, 50, 10);
        }

        // Outline
        this.ctx.strokeStyle = '#000';
        this.ctx.lineWidth = 2;
        this.ctx.beginPath();
        this.ctx.moveTo(0, groundY);
        this.ctx.lineTo(this.canvas.width, groundY);
        this.ctx.stroke();
    }

    drawGameOver() {
        this.ctx.fillStyle = 'rgba(0, 0, 0, 0.7)';
        this.ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);
        
        this.ctx.fillStyle = '#fff';
        this.ctx.strokeStyle = '#000';
        this.ctx.lineWidth = 4;
        this.ctx.font = 'bold 60px Arial';
        this.ctx.textAlign = 'center';
        this.ctx.strokeText('GAME OVER', this.canvas.width / 2, this.canvas.height / 2 - 40);
        this.ctx.fillText('GAME OVER', this.canvas.width / 2, this.canvas.height / 2 - 40);
        
        this.ctx.font = 'bold 36px Arial';
        this.ctx.strokeText(`Score: ${this.score}`, this.canvas.width / 2, this.canvas.height / 2 + 20);
        this.ctx.fillText(`Score: ${this.score}`, this.canvas.width / 2, this.canvas.height / 2 + 20);
        
        this.ctx.font = '24px Arial';
        this.ctx.fillText('Click or Press SPACE to Restart', this.canvas.width / 2, this.canvas.height / 2 + 80);
    }

    gameOver() {
        console.log('Game Over! Score:', this.score);
        this.isGameOver = true;
        this.isRunning = false;
        
        if (typeof submitGameScore === 'function') {
            const user = getCurrentUser();
            if (user) {
                const timePlayed = Math.floor((Date.now() - this.startTime) / 1000);
                submitGameScore('Flappy Bird', this.score, 1, timePlayed);
            }
        }
    }

    restart() {
        console.log('Restarting game...');
        this.reset();
        this.start();
    }

    gameLoop() {
        if (!this.isRunning && !this.isGameOver) {
            // Just draw the start screen
            this.draw();
            this.animationId = requestAnimationFrame(() => this.gameLoop());
            return;
        }
        
        if (this.isRunning) {
            this.update();
        }
        
        this.draw();
        this.animationId = requestAnimationFrame(() => this.gameLoop());
    }

    start() {
        console.log('Starting game...');
        this.startTime = Date.now();
        this.isRunning = true;
        
        if (!this.animationId) {
            this.gameLoop();
        }
    }
    
    stop() {
        console.log('Stopping game...');
        this.isRunning = false;
        if (this.animationId) {
            cancelAnimationFrame(this.animationId);
            this.animationId = null;
        }
    }
}

// Global game instance
let flappyBirdGame = null;

function initFlappy() {
    console.log('=== initFlappy called ===');
    
    // Stop old game if exists
    if (flappyBirdGame) {
        console.log('Stopping old game instance...');
        flappyBirdGame.stop();
        flappyBirdGame = null;
    }
    
    // Small delay to ensure canvas is ready
    setTimeout(() => {
        const canvas = document.getElementById('flappyCanvas');
        console.log('Looking for canvas:', canvas);
        
        if (canvas) {
            console.log('Canvas dimensions:', canvas.width, 'x', canvas.height);
            flappyBirdGame = new FlappyBirdGame('flappyCanvas');
            
            if (flappyBirdGame && flappyBirdGame.canvas) {
                console.log('Game created successfully, starting game loop...');
                flappyBirdGame.start();
            } else {
                console.error('Failed to create game instance');
            }
        } else {
            console.error('Canvas element #flappyCanvas not found in DOM');
        }
    }, 100);
}

console.log('Flappy Bird script loaded');