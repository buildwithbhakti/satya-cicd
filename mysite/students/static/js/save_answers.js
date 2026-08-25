// CSRF token from template
const csrftoken = document.getElementById('csrf_token').value;

// Simple debounce helper
function debounce(fn, wait) {
    let t;
    return function (...args) {
        clearTimeout(t);
        t = setTimeout(() => fn.apply(this, args), wait);
    };
}

async function sendAnswer(element, audio_file = "") {

    const questionId = element.dataset.questionId;
    const testId = element.dataset.testId;
    const questionNo = element.dataset.questionNo;

    const answerStatus = document.getElementById("save-status_" + questionNo)
    const q_type = document.getElementById("q-type_" + questionNo).dataset.info;
    answerStatus.dataset.status = "attempted"
    const status = answerStatus.dataset.status;

    console.log("saving answer...", questionId)
    setStatus(questionNo, 'Saving', 'grey');

    logger.log({
        mode: 'system',
        type: 'info',
        activity: 'Saving answer for question ' + questionNo,
        function_name: 'sendAnswer()'
    });

    // to count the number of words in SA and LA questions
    if (q_type == "SA" || q_type == "LA") {
        no_of_words = element.value.trim().split(/\s+/).filter(Boolean).length;
        document.getElementById('word-count_' + questionNo).textContent = no_of_words;
    }

    try {
        const res = await fetch(save_answer_url, {
            method: 'POST',
            credentials: 'same-origin',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrftoken
            },
            body: JSON.stringify({
                question_id: questionId,
                test_id: testId,
                answer: element.value,
                audio_filename: audio_file,
                answer_status: status
            })
        });
        if (res.ok) {
            setStatus(questionNo, status, 'green');

            logger.log({
                mode: 'system',
                type: 'info',
                activity: 'Saved answer for question ' + questionNo
            });

        } else {
            setStatus(questionNo, 'Error', 'red');

            logger.log({
                mode: 'system',
                type: 'info',
                activity: 'Failed to save answer for question ' + questionNo
            });

        }

    } catch (err) {
        console.error('save answer failed', err);
        setStatus(questionNo, 'Not saved!', 'red');

        logger.log({
            mode: 'system',
            type: 'info',
            activity: 'Failed to save answer for question ' + questionNo
        });

    }
}

// Attach listeners
document.querySelectorAll('.answer-field').forEach(el => {

    const debouncedSend = debounce(() => {
        // el.dataset.status = "attempted";

        sendAnswer(el)

        logger.log({
            mode: 'keyboard',
            type: 'answer',
            activity: 'Answer for question ' + el.dataset.questionNo,
            text: el.value
        });

    }, 800);

    // Prefer input event with debounce for responsive autosave
    el.addEventListener('input', debouncedSend);
});

function setStatus(questionNo, txt, color) {
    const status = document.getElementById('save-status_' + questionNo);
    if (status) {
        status.textContent = txt;
        status.style.color = color || '#666';
    }

    document.getElementById("attempted_question").textContent = getAttemptedQuestions()
}