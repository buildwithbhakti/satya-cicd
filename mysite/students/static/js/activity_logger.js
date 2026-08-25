class ActivityLogger {
    constructor(logUrl, testID) {
        this.logUrl = logUrl;
        this.testID = testID;
        this.queue = [];
        this.batchSize = 10; // Send every 10 logs
        this.flushInterval = 10000; // Or every 10 seconds

        // Auto-flush periodically
        this.timer = setInterval(() => this.flush(), this.flushInterval);

        // Ensure logs are sent when page closes
        window.addEventListener('beforeunload', () => this.flush(true));
        window.addEventListener('visibilitychange', () => {
            if (document.visibilityState === 'hidden') {
                this.flush(true);
            }
        });
    }

    setTestID(testID) {
        this.testID = testID;
    }

    log({
        mode,
        type,
        activity,
        function_name,
        audio_filename = "",
        text = ""
    } = {}) {
        this.queue.push({
            mode,
            type,
            activity,
            function_name,
            audio_filename,
            text,
            test_id: this.testID,
            page: document.title,
            timestamp: localISO
        });
        // Auto-send when batch is full
        if (this.queue.length >= this.batchSize) {
            this.flush();
        }
    }

    flush(isUnloading = false) {
        if (this.queue.length === 0) return;

        const logs = [...this.queue];
        this.queue = [];

        const blob = new Blob([JSON.stringify(logs)], {
            type: 'application/json'
        });

        if (isUnloading) {
            navigator.sendBeacon(this.logUrl, blob);
        } else {
            fetch(this.logUrl, {
                method: 'POST',
                body: blob,
                headers: {
                    'Content-Type': 'application/json'
                },
                keepalive: true
            }).catch(err => {
                console.error('Logging failed:', err);
                this.queue.unshift(...logs); // Retry later
            });
        }
    }
}

// Initialize once when page loads
const logger = new ActivityLogger(log_activity_url, testID);

const now = new Date();
const localISO = new Date(now.getTime() - now.getTimezoneOffset() * 60000).toISOString().slice(0, -1); 



// Add global error handler
class ExamErrorHandler {
  constructor() {
    this.errors = [];
    this.maxErrors = 5;
    
    window.addEventListener('error', (e) => this.handleError(e));
    window.addEventListener('unhandledrejection', (e) => this.handlePromiseRejection(e));
  }

  handleError(event) {
    // console.error('Global error:', event.error);
    
    this.errors.push({
      message: event.error?.message || 'Unknown error',
      stack: event.error?.stack,
    });

    if (this.errors.length >= this.maxErrors) {
      this.showCriticalErrorModal();
    }

    logger.log({
      mode: 'system',
      type: 'error',
      activity: `JavaScript error: ${event.error?.message}`,
      function_name: 'GlobalErrorHandler'
    });

    // Prevent default error handling
    event.preventDefault();

    // interrupt();

  }

  handlePromiseRejection(event) {
    // console.error('Unhandled promise rejection:', event.reason);
    
    logger.log({
      mode: 'system',
      type: 'error',
      activity: `Promise rejection: ${event.reason}`,
      function_name: 'GlobalErrorHandler'
    });
  }

  // showCriticalErrorModal() {
  //   const modal = document.createElement('dialog');
  //   modal.className = 'modal';
  //   modal.innerHTML = `
  //     <div class="modal-box">
  //       <h3 class="text-lg font-bold text-error">System Error</h3>
  //       <p class="py-4">Multiple errors detected. Please wait or refresh the page.</p>
  //       <div class="modal-action">
  //         <button class="btn btn-primary" onclick="location.reload()">Refresh Page</button>
  //       </div>
  //     </div>
  //   `;
  //   document.body.appendChild(modal);
  //   modal.showModal();
  // }

  showCriticalErrorModal() {
    const modal = document.createElement('dialog');
    modal.className = 'modal';
    const modalBox = document.createElement('div');
    modalBox.className = 'modal-box';

    const title = document.createElement('h3');
    title.className = 'text-lg font-bold text-error';
    title.textContent = 'System Error';

    const message = document.createElement('p');
    message.className = 'py-4';
    message.textContent = 'Multiple errors detected. Please wait or refresh the page.';

    const modalAction = document.createElement('div');
    modalAction.className = 'modal-action';

    const refreshBtn = document.createElement('button');
    refreshBtn.className = 'btn btn-primary';
    refreshBtn.textContent = 'Refresh Page';
    refreshBtn.addEventListener('click', function() {
        location.reload();
    });

    // Assemble
    modalAction.appendChild(refreshBtn);
    modalBox.appendChild(title);
    modalBox.appendChild(message);
    modalBox.appendChild(modalAction);
    modal.appendChild(modalBox);

    document.body.appendChild(modal);
    modal.showModal();
  }

}

const errorHandler = new ExamErrorHandler();