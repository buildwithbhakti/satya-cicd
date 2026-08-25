var resume_question = localStorage['resume'] || -1;
var violation_count = 0;
const user = localStorage["user"] || null;
const test = localStorage["test"] || null;
if (user == null || user != userID || test == null || test != testID) {
    localStorage["user"] = userID
    localStorage["test"] = testID
    resume_question = -1
    localStorage['resume'] = -1
} else {
    resume_question = localStorage['resume'] || -1;
}

console.log("previous user: ", user, "current user: ", userID, "test: ", testID);
console.log("Resumed question : ", resume_question);
document.getElementById("attempted_question").textContent = getAttemptedQuestions();

var question_ids = [];

document.querySelectorAll('.questions').forEach(div => {
    question_ids.push(div.id.split("_")[1])
});

console.log("Question Ids: ", question_ids);

logger.log({
    mode: 'system',
    type: 'info',
    activity: 'page load'
});

// **************
// 0: do nothing - for testing
// 1: start from top
// 2: to read - for testing
// 3: to write - for testing
// 4: to resume - for prod.
// ***************

if (exam_mode == "speech" && (test_submitted == "False" || test_retake == "True")) {
    startExam(4);
}

// fine
function startExam(arg) {
    if (arg == 0)
        return
    if (arg == 1)
        startFromTop()
    // readTotalQuestions()
    else if (arg == 2)
        setTimeout(function () {
            readQuestion(1);
        }, 2000);
    else if (arg == 3) {
        audio_wait.pause();
        navigateExam(1, 0)
    } else
        setTimeout(function () {
            if (times_up != true)
                resumeExam();
        }, 1300);
}

const testTime = document.getElementById("test_time");
const tolal_time = humanizeHMS(testTime.textContent)
testTime.innerHTML = tolal_time

// fine
async function startFromTop() {
    logger.log({
        mode: 'system',
        type: 'info',
        activity: 'reading test name and information',
        function_name: "startFromTop()"
    });
    const testname = document.getElementById("test_head").textContent;
    await speak(testname.replace(/\|/g, ','));

    const testInfo = document.getElementById("test_info").textContent;

    await speak(testInfo.replace(/\|/g, ',') + tolal_time);
    readIntro();

}

//fine
async function readIntro() {
    logger.log({
        mode: 'system',
        type: 'info',
        activity: 'reading introduction',
        function_name: "readIntro()"
    });

    await speak(document.getElementById("sayInstructions").textContent);
    await speak(document.getElementById("startExam").textContent);
    instructOrStart()
}

//fine
async function readTotalQuestions() {
    const totalQuestion = document.getElementById("total_questions").textContent;
    logger.log({
        mode: 'system',
        type: 'info',
        activity: 'reading total questions',
        function_name: "readTotalQuestions()"
    });
    await speak(totalQuestion);

    if (getAttemptedQuestions() > 0) {
        const attemptedQuestion = document.getElementById("total_attempted").textContent;
        await speak(attemptedQuestion);
    }

    readGeneralInstructions(1);
}

// fine
async function instructOrStart() {
    const asr_out = await getReply();

    logger.log({
        mode: 'system',
        type: 'info',
        activity: 'instruction or start command',
        text: asr_out,
        function_name: "instructOrStart()",
    });

    if (asr_out.includes("instructions")) {
        if (asr_out.includes("exam")) {
            var testhead2 = document.getElementById("general-instructions").textContent;
            await speak(testhead2);
            readIntro();
        } else if (asr_out.includes("system")) {
            var testhead2 = document.getElementById("instructions").textContent;
            await speak(testhead2);
            readIntro();
        } else {
            await speak(msg_sorryMsg);
            readIntro();
        }

    } else if (asr_out.includes("start exam")) {
        readTotalQuestions();
    } else {
        await speak(msg_sorryMsg);
        instructOrStart();
    }
}

// test
async function resumeExam() {

    if (resume_question != -1) {
        const msg = msg_qNo + " " + Object.values(question_ids)[resume_question - 1] + msg_rsmYN;
        document.getElementById("resume_modal_text").innerHTML = msg
        resumeModal.showModal();


        if (audioModal.open) {
            audioModal.close();
            audioModal.showModal();
        }

        const reply = await speakAndGetReply(msg)

        if (reply.includes("yes")) {
            logger.log({
                mode: 'speech',
                type: 'command',
                activity: 'resume exam yes',
                function_name: "resumeExam()"
            });
            resumeExamYes()

        } else if (reply.includes("no")) {
            logger.log({
                mode: 'speech',
                type: 'command',
                activity: 'resume exam no',
                function_name: "resumeExam()"
            });
            resumeExamNo()
        } else {
            await speak(msg_sorryMsg);
            resumeModal.close();
            readTotalQuestions()
        }
    } else {
        readTotalQuestions()
    }
}


function resumeExamYes() {
    resumeModal.close();
    // document.getElementById("attempted_question").textContent = getAttemptedQuestions()
    readQuestion(resume_question)
}

function resumeExamNo() {
    // this leads to insconsistecy because the reset changes are note saved in the database.
    // document.querySelectorAll('.answer-field').forEach(field => {
    //     console.log("clearing the fields")
    //     if (field.tagName === 'TEXTAREA') {
    //         field.value = '';
    //     } else if (field.type === 'radio') {
    //         field.checked = false;
    //     } else if (field.type === 'checkbox') {
    //         field.checked = false;
    //     }
    // });
    // document.querySelectorAll('.status-field').forEach(field => {
    //     field.textContent = ''
    //     field.dataset.status = "unattempted"
    // });
    // resumeModal.close();
    // updateDots()
    resumeModal.close();
    startFromTop();
}

document.getElementById("resume_modal_yes").addEventListener("click", () => {
    logger.log({
        mode: 'keyboard',
        type: 'command',
        activity: 'resume exam yes'
    });
    resumeExamYes()
});

document.getElementById("resume_modal_no").addEventListener("click", () => {
    logger.log({
        mode: 'keyboard',
        type: 'command',
        activity: 'resume exam no'
    });
    resumeExamNo()
});


async function readGeneralInstructions(qNo) {
    logger.log({
        mode: 'speech',
        type: 'info',
        activity: 'read exam instructions',
        function_name: "readGeneralInstructions()"
    });
    if (test_instructions.trim() != "") {
        const generalInstructions = document.getElementById("general-instructions").textContent;
        await speak(generalInstructions);
    }
    readQuestion(qNo);
}


var col_a_text, col_b_text;
// fine
async function readQuestion(qNo) {

    document.getElementById("attempted_question").innerHTML = getAttemptedQuestions()
    var addSynth = "";
    var ques = "";
    var qtype = "";
    var attempted = false;
    qNo = parseInt(qNo);
    lastPlayedQuestion = qNo;
    console.log("question no. ", qNo, " / ", question_count);
    // for question > last question
    if (qNo > question_count) {

        qtype = "INVALID_LAST"
        console.log("LAST QUESTION")

    } // for question < first question
    else if (qNo < 1) {
        qNo = 1
        qtype = "INVALID_FIRST"
        console.log("FIRST QUESTION")

    } else {
        const ques_element = document.getElementById("question_" + qNo);
        audio_file_name = document.getElementById("question_" + qNo).dataset.audio;
        console.log("Audio file name: ", audio_file_name);
        qtype = document.getElementById("q-type_" + qNo).dataset.info;
        attempted = document.getElementById("save-status_" + qNo).dataset.status == "attempted";
        //scroll to question
        ques = (ques_element.textContent.replace(/\s+/g, ' ').trim())
        ques_element.scrollIntoView();

        localStorage['resume'] = qNo;
        console.log("Current question : ", localStorage['resume'], qtype);

        goTo(qNo - 1, 'speech')
    }

    // for last question
    if (question_count === qNo && qtype != "INVALID_FIRST" && qtype != "INVALID_LAST") {
        addSynth += msg_finalQuestion + msg_previousQuestion + msg_submitTest;
    }

    // console.log("Type of Question : ", qtype);
    if (qtype == "SA" || qtype == "LA") {
        console.log("inside desc");
        if (attempted) {

            addSynth = msg_reviewSaLaFib;

        } else {

            addSynth += msg_sayWrite;

        }

    } else if (qtype == "MCQ") {
        console.log("inside objecive");
        if (attempted) {

            const selected = document.querySelector(
                `input[name="q-options_${qNo}"]:checked`
            );

            if (selected) {

                const optionNo = selected.id.split("_").pop();

                const label = document.querySelector(
                    `label[for="${selected.id}"]`
                );

                const optionText = label ? label.textContent.trim() : "";

                addSynth = msg_alrdy_answrd + " " + optionNo + ", " + optionText + " " + msg_reviewMCQ;

            } else {

                addSynth = msg_reviewSaLaFib;

            }

        } else {

            addSynth += msg_sayOption;

        }
    } else if (qtype == "TF") {
        console.log("inside T/F");
        if (attempted) {

            const selected = document.querySelector(
                `input[name="q-options_${qNo}"]:checked`
            );

            if (selected) {

                const label = document.querySelector(
                    `label[for="${selected.id}"]`
                );

                const optionText = label ? label.textContent.trim() : "";

                addSynth = msg_alrdy_answrd + " " + optionText + " " + msg_reviewTF;

            } else {

                addSynth = msg_reviewSaLaFib;

            }

        } else {

            addSynth += msg_sayTF;

        }
    } else if (qtype == "FIB") {
        console.log("inside Fill in Blanks");
        ques = ques.replace("______", " dash ")
        if (attempted) {

            addSynth = msg_reviewSaLaFib;

        } else {

            addSynth += msg_sayWrite;

        }

    } else if (qtype == "MSQ") {

        console.log("inside multiple selection");

        if (attempted) {

            const selectedOptions = document.querySelectorAll(
                `input[name="q-options_${qNo}"]:checked`
            );

            if (selectedOptions.length > 0) {

                let selectedText = [];

                selectedOptions.forEach(option => {

                    const optionNo =
                        option.id.split("_").pop();

                    const label = document.querySelector(
                        `label[for="${option.id}"]`
                    );

                    const optionText =
                        label ? label.textContent.trim() : "";

                    selectedText.push(
                        "Option " + optionNo + ", " + optionText
                    );

                });

                addSynth +=
                    "You have already selected the following options. " +
                    selectedText.join(". ") +
                    ". Say read answer to hear your complete answer. " +
                    "Say option followed by the option number to update your answer. " +
                    "Otherwise, say the next command.";

            } else {

                addSynth +=
                    "You have already answered this question. " +
                    "Say read answer to hear your answer. " +
                    "Say option followed by the option number to update your answer. " +
                    "Otherwise, say the next command.";

            }

        } else {

            addSynth += msg_sayOption;

        }

    } else if (qtype == "MTF") {
        col_a_text = ""
        col_b_text = ""
        console.log("inside Match the following");

        // ques = ques.replace(/(Marks:\s*\[\d+\])[\s\S]*$/i, '$1').trim();
        // quick fix
        ques = ques.replace(/((?:Marks|गुण):\s*\[\d+\])[\s\S]*$/i, '$1').trim();

        ques += msg_instrMTF;

        const col_a_span = document.querySelectorAll(`span[name="${qNo}_col_a"]`);
        col_a_text = Array.from(col_a_span, s => s.textContent.trim());
        ques += "\n ." + msg_clmA + ". \n"
        for (let i = 0; i < col_a_text.length; i++) {
            ques += i + 1 + ". " + col_a_text[i] + "\n";
        }

        const col_b_span = document.querySelectorAll(`span[name="${qNo}_col_b"]`);
        const col_b_text_tmp = Array.from(col_b_span, s => s.textContent.trim());
        col_b_text = Array.from(new Set(col_b_text_tmp));
        ques += "\n ." + msg_clmB + ". \n"
        for (let i = 0; i < col_b_text.length; i++) {
            ques += i + 1 + ". " + col_b_text[i] + "\n";
        }

        addSynth += msg_selMTF;
        // for testing
        // MatchPairAnswer(qNo)

    } else if (qtype == "INVALID_LAST") {
        addSynth += msg_finalQuestion + msg_sayHelp + msg_sayExamStatus;
        qNo = question_count

    } else if (qtype == "INVALID_FIRST") {
        addSynth += msg_fstQue + msg_sayHelp + msg_sayExamStatus + msg_nextQuestion

    } else {
        addSynth += msg_sorryMsg;

    }

    console.log("QUES : ", ques + " SYNTH: " + addSynth);

    logger.log({
        mode: 'system',
        type: 'info',
        activity: 'reading question for question no ' + qNo,
        function_name: "readQuestion()",
    });

    if (ques != "") {
        await speak(ques);
    }

    await speak(addSynth);
    navigateExam(qNo, 0);
}

function cleanText(str) {
    return str
        .trim() // remove leading/trailing whitespace from the whole string
        .split(/\r?\n/) // split into lines
        .map(line => line.trim()) // remove leading/trailing whitespace from each line
        .filter(line => line !== '') // remove blank lines
        .map(line => line.replace(/ {2,}/g, ' ')) // collapse 2+ spaces into one
        .join(', ') // rejoin lines
        .trim();
}

var navQus = 0;
// core engine 
async function navigateExam(qNo, navQus) {

    console.log("speechQuestion :: qNo : " + qNo);

    const asr_out = await getReply()

    var qtype = document.getElementById("q-type_" + qNo).dataset.info;

    console.log(eventCount, " :: speech text : ", asr_out)
    console.log("Q no :", qNo, " Q Type :", qtype);


    if (asr_out == "repeat") {
        console.log("inside repeat question");
        reapeatQuestion(qNo);
    } else if (asr_out.includes("instructions")) {
        if (asr_out.includes("general")) {
            readGeneralInstructions(qNo);
        } else if (asr_out.includes("system")) {
            var testhead2 = document.getElementById("instructions").textContent;
            await speak(testhead2);
            readQuestion(qNo);
        } else {
            await speak(msg_sorryMsg);
            await speak(document.getElementById("sayInstructions").textContent);
            navigateExam(qNo, 0);
        }
    } else if (asr_out.includes("option") && ((qtype == "MCQ") || (qtype == "MSQ"))) {
        console.log("inside objective option");
        writeObjectiveAnswer(qNo, asr_out);
    } else if ((asr_out.includes("true") || asr_out.includes("2") || asr_out.includes("false")) && qtype == "TF") {
        console.log("inside true false");
        writeTrueFalseAnswer(qNo, asr_out);

    } else if (asr_out.includes("write") && (qtype == "SA" || qtype == "LA")) {
        console.log("Inside descriptive write answer!");
        writeAnswer(qNo);
    } else if (asr_out.includes("write") && qtype == "FIB") {
        console.log("Inside FIB write answer!");
        writeFillInBlank(qNo);
    } else if (asr_out == "exam status") {
        console.log("inside exam status");
        examStatus(qNo);
    } else if (asr_out.includes("status")) {
        console.log("Inside answer status!");
        updateQuestionStatus(qNo, asr_out);
    } else if (asr_out.includes("next question") || asr_out.includes("next")) {
        console.log("inside next question");
        moveNextQuestion(qNo);
    } else if (asr_out.includes("previous question")) {
        console.log("inside previous question");
        movePreviousQuestion(qNo);
    } else if (asr_out.includes("question")) {
        navigateQuestion(qNo, asr_out);
    } else if (asr_out.includes("read answer")) {
        console.log("inside read answer");
        readAnswer(qNo);
    } else if (asr_out == "instruction" || asr_out == "instructions") {
        console.log("inside instuctions")
        readInstructions(qNo);
    } else if (asr_out == "time remaining") {
        console.log("inside time");
        readTimeRemaining(qNo);
    } else if (asr_out == "help") {
        console.log("inside help");
        helpSection(qNo);
    } else if (asr_out.includes("delete") && (qtype == "SA" || qtype == "LA" || qtype == "FIB")) {
        console.log("Inside delete!");
        deleteAnswer(qNo, asr_out);
    } else if (asr_out.includes("highlight") && (qtype == "SA" || qtype == "LA")) {
        console.log("Inside emphasize!");
        emphasizeAnswer(qNo, asr_out);
    } else if (asr_out.includes("replace") && (qtype == "SA" || qtype == "LA")) {
        console.log("Inside replace!");
        replaceAnswer(qNo, asr_out);
    } else if (asr_out.includes("matching") && (qtype == "MTF")) {
        console.log("Inside Match the follwoing!");
        MatchPairAnswer(qNo, asr_out);
    } else if (asr_out == "submit") {
        console.log("inside submit")
        checkSubmit(qNo);
    } else if (asr_out.includes("count words") && (qtype == "SA" || qtype == "LA")) {
        console.log("inside word count")
        wordCount(qNo);
    } else if (asr_out.includes("review")) {
        console.log("Inside mark review!");
        handleMarkReview(qNo, asr_out);
    } else if (asr_out.includes("note")) {
        console.log("Inside note!");
        handleNotes(qNo, asr_out);
    } else {
        console.log("inside fallbacked..");
        fallbackCase(qNo, asr_out);
    }

    function moveNextQuestion(qNo) {
        qNo++;
        logger.log({
            mode: 'speech',
            type: 'command',
            activity: 'Move to next question ' + qNo,
            text: speechResult,
            function_name: "moveNextQuestion()"
        });
        readQuestion(qNo);
    }

    function movePreviousQuestion(qNo) {
        qNo--;
        logger.log({
            mode: 'speech',
            type: 'command',
            activity: 'Move to previous question ' + qNo,
            text: speechResult,
            function_name: "movePreviousQuestion()"
        });
        readQuestion(qNo);
    }

    function reapeatQuestion(qNo) {
        logger.log({
            mode: 'speech',
            type: 'command',
            activity: 'Repeating question ' + qNo,
            text: speechResult,
            function_name: "repeatQuestion()"
        });
        readQuestion(qNo);
    }
}

async function handleNotes(qNo, speechResult) {
    showQuestionNoteModal(qNo);

    if (speechResult.includes("add")) {
        const asr_out = await speakAndGetReply("Write your note", {
            lang: langcode,
            server: "bhashini",
            max_wait_seconds: 2,
            color: "green"
        })
        questionNoteText.value += asr_out + "\n";
        saveNote(qNo, "speech")
        await speak("Note added");
    } else if (speechResult.includes("clear")) {
        questionNoteText.value = "";
        saveNote(qNo, "speech")
        await speak("Note cleared");
    } else if (speechResult.includes("read")) {
        await speak(questionNoteText.value);
        saveNote(qNo, "speech")
    } else {
        await speak(msg_sorryMsg);
        saveNote(qNo, "speech")
    }
    navigateExam(qNo)

}

async function handleMarkReview(qNo, speechResult) {
    if (speechResult.includes("mark")) {
        updateQuestionReview(qNo, "speech")
        await speak("Question " + qNo + " marked for review");
        await speak(msg_sayCommand);
        navigateExam(qNo)
    } else if (speechResult.includes("clear")) {
        updateQuestionReview(qNo, "speech")
        await speak("Question " + qNo + " cleared from review");
        await speak(msg_sayCommand);
        navigateExam(qNo)
    } else if (speechResult.includes("all")) {
        question_to_review = document.getElementById('review_questions_display_text').textContent
        
        if(document.getElementById('review_questions_display').textContent == ""){
            await speak("No questions marked for review");
        }else{
            await speak(question_to_review);
            await speak("Say question number to navigate to that question");
        }
        navigateExam(qNo)
    } else {
        await speak(msg_sorryMsg);
        navigateExam(qNo)
    }
}

async function wordCount(qNo) {
    logger.log({
        mode: "speech",
        type: 'command',
        activity: 'word count for question ' + qno + ' - ',
        function_name: "wordCount()"
    });

    await speak(document.getElementById("word-count_" + qNo).textContent);
    await speak(msg_sayCommand);
    navigateExam(qNo)
}

// re code
async function readTimeRemaining(qNo) {
    logger.log({
        mode: 'speech',
        type: 'command',
        activity: 'Reading time remaining ' + countdownEl.textContent,
        text: speechResult,
        function_name: "readTimeRemaining()"
    });
    await speak(countdownEl.textContent);
    readQuestion(qNo);

}

// test
async function writeObjectiveAnswer(qNo, speechResult) {
    write_answer_split = speechResult.split(" ");

    logger.log({
        mode: 'speech',
        type: 'answer',
        activity: 'Objective answer for question ' + qNo,
        text: speechResult,
        function_name: "writeObjectiveAnswer()"
    });

    if (write_answer_split.length > 1) {

        var optionNo = write_answer_split[1].replace(/[.,]/g, '').toLowerCase().trim();

        if (optionNo >= 1 && optionNo <= 6)
            saveAnswer(qNo, optionNo, speechResult);
        else {

            asr_out = await resendToTranscribe()
            trimmed_text = asr_out.split(" ").slice(1).join(" ");
            console.log("trimmed output:" + trimmed_text);

            const radios = document.querySelectorAll(`input[name="q-options_${qNo}"]`);
            option_found = false

            radios.forEach(radio => {
                const label = document.querySelector(`label[for="${radio.id}"]`);
                const labelText = label ? label.textContent.trim() : '';

                if (labelText.toLowerCase().trim() == trimmed_text.toLowerCase().trim()) {
                    // radio.checked = true;
                    // extract option number from id: q_{questionCounter}-options_{optionNo}
                    const match = radio.id.match(/-options_(\d+)$/);
                    selectedOptionNo = match ? parseInt(match[1], 10) : null;
                    saveAnswer(qNo, selectedOptionNo, speechResult);
                    option_found = true
                }
            });

            if (option_found == false) {
                await speak(msg_noOpt)
                readQuestion(qNo);
            }

        }
    } else {
        await speak(msg_spkAgn);
        navigateExam(qNo)
    }
}

async function writeTrueFalseAnswer(qNo, speechResult) {

    logger.log({
        mode: 'speech',
        type: 'answer',
        activity: 'True/False answer for question ' + qNo,
        text: speechResult,
        function_name: "writeTrueFalseAnswer()"
    });

    if (speechResult == "true" || speechResult == "2") {
        saveAnswer(qNo, 1, speechResult);
    } else if (speechResult == "false") {
        saveAnswer(qNo, 2, speechResult);
    } else {
        await speak(msg_noOpt)
        readQuestion(qNo);
    }
}

// fine
async function writeAnswer(qNo) {
    const asr_out = await speakAndGetReply(msg_writeYourAns, {
        lang: langcode,
        server: "bhashini",
        max_wait_seconds: 5,
        color: "green"
    })
    console.log("ID: ", "answer_" + qNo);
    logger.log({
        mode: 'speech',
        type: 'answer',
        activity: 'Descriptive answer for question ' + qNo,
        text: asr_out,
        audio_filename: audio_filename,
        function_name: "writeAnswer()"
    });
    if (asr_out == "error-500") {
        await speak(msg_sorryMsg + ", " + msg_sayCommand);
        navigateExam(qNo, 0);
    } else {
        document.getElementById("answer_" + qNo).value += asr_out + "\n";
        saveAnswer(qNo, -1, asr_out);
    }
}

async function writeFillInBlank(qNo) {
    const asr_out = await speakAndGetReply(msg_writeYourAns, {
        lang: langcode,
        server: "bhashini",
        max_wait_seconds: 2,
        color: "green"
    })
    console.log("ID: ", "answer_" + qNo);
    logger.log({
        mode: 'speech',
        type: 'answer',
        activity: 'Fill in the blank answer for question ' + qNo,
        text: asr_out,
        audio_filename: audio_filename,
        function_name: "writeFillInBlank()"
    });
    console.log("ID: ", "answer_" + qNo);
    document.getElementById("answer_" + qNo).value += asr_out + "\n";
    saveAnswer(qNo, -1, asr_out);
}

// test
async function updateQuestionStatus(qNo, speechResult) {

    logger.log({
        mode: 'speech',
        type: 'answer',
        activity: 'Update question status for question ' + qNo,
        text: speechResult,
        audio_filename: audio_filename,
        function_name: "updateQuestionStatus()"
    });

    statusKeyword_status = speechResult.split(" ");

    answer = document.getElementById("answer_" + qNo);
    answer_status = statusKeyword_status[1].replace(/[.,]/g, '').toLowerCase().trim();
    if (answer_status == "unattempted" || answer_status == "attempted") {
        sendAnswer(answer, "", answer_status)
        await speak("saved")
    } else {
        await speak("saved")
        readQuestion(qNo);
    }
}

// re code
async function navigateQuestion(qNo, speechResult) {
    // use bhasini api for question based nevigation

    console.log("ID: ", "answer_" + qNo);

    logger.log({
        mode: 'speech',
        type: 'info',
        activity: 'navigation using question no',
        text: speechResult,
        function_name: "navigateQuestion()"
    });

    question_no = speechResult.split(" ")[1]

    if (question_ids.includes(question_no)) {
        console.log("found question no. ", question_no)
        readQuestion(question_no);
    } else if (question_no > question_count) {
        await speak(msg_noQue);
        readQuestion(qNo);
    } else {
        await speak(msg_sorryMsg);
        readQuestion(qNo);
    }

}

// fine
// async function readAnswer(qNo) {

//     logger.log({
//         mode: 'speech',
//         type: 'info',
//         activity: 'read answer for question ' + qNo,
//         function_name: "readAnswer()"
//     });

//     var answer = document.getElementById("answer_" + qNo).value + msg_sayCommand;
//     console.log("answer", answer)
//     await speak(answer)
//     navigateExam(qNo);
// }

async function readAnswer(qNo) {

    logger.log({
        mode: 'speech',
        type: 'info',
        activity: 'read answer for question ' + qNo,
        function_name: "readAnswer()"
    });

    const qtype = document.getElementById("q-type_" + qNo).dataset.info;

    let answer = "";
    let answerPrefix = "";
    let updateInstruction = "";

    // --------------------------
    // SA / LA / FIB
    // --------------------------
    if (qtype == "SA" || qtype == "LA" || qtype == "FIB") {

        answer = document.getElementById("answer_" + qNo).value.trim();

        if (answer != "") {
            answerPrefix = "Your written answer is.";
            updateInstruction =
                "To update your answer, say write answer.";
        }

    }
    // --------------------------
    // MCQ
    // --------------------------
    else if (qtype == "MCQ") {

        const selected = document.querySelector(
            `input[name="q-options_${qNo}"]:checked`
        );

        if (selected) {

            const optionNo = selected.id.split("_").pop();

            const label = document.querySelector(
                `label[for="${selected.id}"]`
            );

            const optionText = label ? label.textContent.trim() : "";

            answerPrefix =
                "You had selected option " +
                optionNo +
                ", " +
                optionText + ".";

            updateInstruction =
                "To change your answer, say option followed by the option number.";

        }

    }

    // --------------------------
    // TRUE / FALSE
    // --------------------------
    else if (qtype == "TF") {

        const selected = document.querySelector(
            `input[name="q-options_${qNo}"]:checked`
        );

        if (selected) {

            const label = document.querySelector(
                `label[for="${selected.id}"]`
            );

            const optionText = label ? label.textContent.trim() : "";

            answerPrefix =
                "You had selected " +
                optionText + ".";

            updateInstruction =
                "To change your answer, say True or False.";

        }

    }
    // --------------------------
    // MSQ
    // --------------------------
    else if (qtype == "MSQ") {

        const selectedOptions = document.querySelectorAll(
            `input[name="q-options_${qNo}"]:checked`
        );

        if (selectedOptions.length > 0) {

            let selectedText = [];

            selectedOptions.forEach(option => {

                const optionNo =
                    option.id.split("_").pop();

                const label = document.querySelector(
                    `label[for="${option.id}"]`
                );

                const optionText =
                    label ? label.textContent.trim() : "";

                selectedText.push(
                    "Option " + optionNo + ", " + optionText
                );

            });

            answerPrefix =
                "You had selected the following options.";

            answer =
                selectedText.join(". ");

            updateInstruction =
                "To change your answer, say option followed by the option number.";

        }

    }
        // --------------------------
    // MTF
    // --------------------------
    else if (qtype == "MTF") {

        const colA = document.querySelectorAll(
            `span[name="${qNo}_col_a"]`
        );

        const colB = document.querySelectorAll(
            `span[name="${qNo}_col_b"]`
        );

        let matches = [];

        for (let i = 0; i < colA.length; i++) {

            const radioName =
                `q_${qNo}-choices_${i + 1}`;

            const selected = document.querySelector(
                `input[name="${radioName}"]:checked`
            );

            if (selected) {

                const selectedOptionNo =
                    parseInt(
                        selected.id.split("-").pop()
                    ) - 1;

                const leftText =
                    colA[i].textContent.trim();

                const rightText =
                    colB[selectedOptionNo].textContent.trim();

                matches.push(
                    leftText +
                    " matched with " +
                    rightText
                );

            }

        }

        if (matches.length > 0) {

            answerPrefix =
                "Your saved matching is.";

            answer =
                matches.join(". ");

            updateInstruction =
                "To change your answer, say matching followed by the row number and option number.";

        }

    }

    // --------------------------
    // No answer
    // --------------------------
    if (
        answer == "" &&
        answerPrefix == ""
    ) {

        await speak("No answer has been given.");

    } else {

        if (answerPrefix != "")
            await speak(answerPrefix);

        if (answer != "")
            await speak(answer);

        await speak(updateInstruction);

        await speak(
            "Otherwise, say the next command to continue the exam."
        );

    }

    navigateExam(qNo, 0);

}

// fine
async function readInstructions(qNo) {

    logger.log({
        mode: 'speech',
        type: 'info',
        activity: 'read instructions',
        function_name: "readInstructions()"
    });

    var instructions = document.getElementById("instructions").textContent;

    await speak(instructions)
    readQuestion(qNo);
}

// test
async function helpSection(qNo) {
    const asr_out = await speakAndGetReply(document.getElementById("sayInstructions").textContent)
    logger.log({
        mode: 'speech',
        type: 'info',
        activity: 'help section',
        text: asr_out,
        function_name: "helpSection()"
    });

    if (asr_out.includes("exam")) {
        var testhead2 = document.getElementById("general-instructions").textContent;
        await speak(testhead2);
        readQuestion(qNo)
    } else if (asr_out.includes("system")) {
        var testhead2 = document.getElementById("instructions").textContent;
        await speak(testhead2);
        readQuestion(qNo)
    } else {
        await speak(msg_sorryMsg);
        helpSection(qNo)
    }
}

// test
async function examStatus(qNo) {

    logger.log({
        mode: 'speech',
        type: 'info',
        activity: 'exam status',
        function_name: "examStatus()"
    });

    total_questions = document.getElementById("total_questions").textContent;
    total_attempted = document.getElementById("total_attempted").textContent;

    // console.log(countsString);
    msg = total_questions + ". " + total_attempted

    await speak(msg)
    navigateExam(qNo, 0);
}



// fine
async function fallbackCase(qNo, speechResult) {
    logger.log({
        mode: 'speech',
        type: 'info',
        activity: 'no match for command',
        text: speechResult,
        function_name: "fallbackCase()"
    });
    await speak(msg_sorryMsg)
    navigateExam(qNo, 0);
}

// test
async function deleteAnswer(qNo, speechResult) {

    logger.log({
        mode: 'speech',
        type: 'info',
        activity: 'delete answer for question ' + qNo,
        text: speechResult,
        function_name: "deleteAnswer()"
    });

    delete_string = speechResult.split(" ");
    if (delete_string.length > 1) {

        deleteKeyword = delete_string[1].replace(/[.,]/g, '').toLowerCase().trim();
        if (deleteKeyword == "answer") {
            document.getElementById("answer_" + qNo).value = " ";
            saveAnswer(qNo, -2, msg_ansDltd)
        } else if (deleteKeyword == "point") {
            textarea = document.getElementById("answer_" + qNo).value;
            var lines = textarea.split('\n');
            lines.pop();
            lines.pop();
            var newText = lines.join('\n') + "\n";
            document.getElementById("answer_" + qNo).value = newText;
            saveAnswer(qNo, -3, newText)
        } else {
            await speak(msg_noOprtn);
            navigateExam(qNo, 0);
        }
    } else {
        await speak(msg_spkAgn)
        navigateExam(qNo, 0);
    }
}

// experimental
async function emphasizeAnswer(qNo, speechResult) {

    const asr_out = await speakAndGetReply(msg_hlghtWrd, {
        lang: langcode,
        server: "bhashini",
        max_wait_seconds: 2,
        color: "green"
    })
    const keyword = asr_out.toLowerCase().trim()

    logger.log({
        mode: 'speech',
        type: 'info',
        activity: 'read instructions',
        text: asr_out,
        audio_filename: audio_filename,
        function_name: "emphasizeAnswer()"
    });

    var answer_to_emhasize = document.getElementById("answer_" + qNo)
    var written_answer = answer_to_emhasize.innerHTML;
    if (written_answer.includes(keyword)) {
        speechResult_bold = "<b>" + keyword + "</b>"
        res = written_answer.replace(keyword, speechResult_bold)
        answer_to_emhasize.innerHTML = res;
        await speak(keyword + ", is highlighted" + msg_sayCommand);
        navigateExam(qNo)

    } else {
        console.log(msg_sryNtFound + keyword);
        await speak(msg_sryNtFound + "," + keyword + "," + msg_sayCommand);
        navigateExam(qNo)
    }
}

// to test
async function replaceAnswer(qNo, speechResult) {

    const asr_out = await speakAndGetReply("speak the word to replace", {
        lang: langcode,
        server: "bhashini",
        max_wait_seconds: 2,
        color: "green"
    })
    const keyword = asr_out.toLowerCase().trim()

    logger.log({
        mode: 'speech',
        type: 'info',
        activity: 'read instructions',
        text: asr_out,
        audio_filename: audio_filename,
        function_name: "replaceAnswer()"
    });

    var answer_to_repalce = document.getElementById("answer_" + qNo)
    var written_answer = answer_to_repalce.innerHTML;
    if (written_answer.includes(keyword)) {

        const asr_out = await speakAndGetReply("say the new text", {
            lang: langcode,
            server: "bhashini",
            max_wait_seconds: 2,
            color: "green"
        })
        const new_text = asr_out.toLowerCase().trim()


        res = written_answer.replace(keyword, new_text)
        answer_to_repalce.innerHTML = res;
        await speak(keyword + ", is replaced with, " + new_text + "," + msg_sayCommand);

        saveAnswer(qNo, -1, res);

    } else {
        console.log(msg_sryNtFound + keyword);
        await speak(msg_sryNtFound + "," + keyword + "," + msg_sayCommand);
        navigateExam(qNo)
    }
}

// test
async function MatchPairAnswer(qNo) {
    choice_to_speak = ""
    for (let i = 0; i <= col_a_text.length; i++) {
        if (i == col_a_text.length) {
            await speak(msg_sayCommand)
            navigateExam(qNo, 0);
            break;
        }
        choice_to_speak = "\n" + msg_clmA + ", \n"
        choice_to_speak += col_a_text[i] + "\n" + msg_clmB + ",\n"

        for (let j = 0; j < col_b_text.length; j++) {
            choice_to_speak += j + 1 + ", " + col_b_text[j] + "\n"
        }
        // [enhancement] inculde last choice text to the user instead of msg_nxtChoice   
        choice_to_speak += msg_nxtChoice;
        console.log(choice_to_speak)

        const reply = await speakAndGetReply(choice_to_speak);

        logger.log({
            mode: 'speech',
            type: 'answer',
            activity: 'matching pair answer for question ' + qNo,
            text: reply,
            function_name: "MatchPairAnswer()"
        });

        if (reply.includes("next")) {
            continue

        } else if (reply.includes("option")) {
            optionKeyword_optionNo = reply.split(" ");
            if (optionKeyword_optionNo.length > 1) {
                var optionNo = optionKeyword_optionNo[1].replace(/[.,]/g, '').toLowerCase().trim();

                if (optionNo >= 1 && optionNo <= 6) {
                    console.log("col_b_text:", col_b_text)
                    radio_name = "q_" + qNo + "-choices_" + Number(i + 1)
                    radios = document.getElementsByName(radio_name);
                    selected_option_no = optionNo - 1
                    radios[selected_option_no].checked = true;

                    radio_id = document.getElementById(radio_name + "-" + optionNo)
                    sendAnswer(radio_id)
                    await speak(msg_uSlctd + col_b_text[selected_option_no]);

                } else {
                    await speak(msg_noOpt);
                    i--
                }

            } else {
                await speak(msg_spkAgn);
                navigateExam(qNo)
            }

        } else if (reply.includes("repeat")) {
            i--
        } else if (reply.includes("previous")) {
            i = i - 2
        } else if (reply == "previous question") {
            readQuestion(qNo - 1)

        } else if (reply == "next question") {
            readQuestion(qNo + 1)

        } else {
            await speak(msg_sorryMsg);
            readQuestion(qNo)
        }
    }
}

// verify
async function saveAnswer(qNo, qType, speechResult) {

    console.log("question no " + qNo + " qestion type " + qType);

    var your_answer
    // if qType = -1 the question is descriptive otherwise objective
    if (qType == -1) {
        // for descriptive
        save_answer = document.getElementById("answer_" + qNo);
        your_answer = msg_wrtnAns + speechResult;
        console.log("here ", your_answer)

    } else if (qType == -2) {
        // for deletion
        save_answer = document.getElementById("answer_" + qNo);
        your_answer = msg_ansDltd;

    } else if (qType == -3) {
        // for deletion
        save_answer = document.getElementById("answer_" + qNo);
        your_answer = msg_pntDltd;
    } else {
        //for objective
        save_answer = document.getElementById("q_" + qNo + "-options_" + qType);
        // for selecting radio button
        console.log("q_" + qNo + "-options_" + qType);
        radios = document.getElementsByName("q-options_" + qNo);
        var option_speak = ""
        if (radios[qType - 1].checked) {
            radios[qType - 1].checked = false;
            option_speak = msg_unslctd;
        } else {
            radios[qType - 1].checked = true;
            option_speak = msg_slctd;
        }
        // for speak
        var mcq_label = "q_" + qNo + "-options_" + qType
        console.log(mcq_label)
        const label = document.querySelector(`label[for="${mcq_label}"]`);
        const labelText = label ? label.textContent.trim() : '';
        your_answer = option_speak + (qType) + " " + labelText;
    }

    // save_answer.dataset.status = "attempted";


    logger.log({
        mode: 'speech',
        type: 'answer',
        activity: 'Answer for question ' + qNo,
        function_name: "saveAnswer()",
        text: your_answer
    });

    sendAnswer(save_answer, audio_filename)
    await speak(your_answer + msg_sayCommand)
    navigateExam(qNo, 0);

}

function getAttemptedQuestions() {
    const attempted = document.querySelectorAll('.status-field[data-status="attempted"]');
    return attempted.length;
}

function getUnattemptedQuestions() {
    const attempted = document.querySelectorAll('.status-field[data-status="unattempted"]');
    const questionNumbers = Array.from(attempted).map(el => el.dataset.questionNo);
    return questionNumbers.length > 0 ? questionNumbers.join(", ") : 0;
}

// verify
async function checkSubmit(qNo) {

    submitModalShow();

    const reply = await speakAndGetReply(document.getElementById("submit_msg").textContent + ". " + msg_sbmtYN)
    if (reply.includes("yes")) {
        logger.log({
            mode: 'speech',
            type: 'command',
            activity: 'Submit Exam - yes',
            function_name: "checkSubmit()"
        });
        submitExam();
    } else if (speechResult.includes("no")) {
        logger.log({
            mode: 'speech',
            type: 'command',
            activity: 'Submit Exam - no',
            function_name: "checkSubmit()"
        });
        await speak("say question followed by question number to navigate to that question.");
        navigateExam(qNo, 0)
        submitModal.close();
    } else {
        await speak(msg_sorryMsg)
        submitExam(qNo)
    }
}

// function submitModalShow() {
//     ques = getUnattemptedQuestions()
//     console.log("Unattempted questions : ", ques)
//     if (ques == 0) {
//         msg = all_attempted;
//     } else {
//         msg = msg_nt_ansrd + " " + ques;
//     }
//     document.getElementById("submit_msg").textContent = msg
//     submitModal.showModal();
// }

function submitModalShow() {

    ques = getUnattemptedQuestions();
    console.log("Unattempted questions : ", ques);

    if (ques == 0) {
        msg = all_attempted;
    } else {
        msg = msg_nt_ansrd + " " + ques;
    }

    if (exam_mode == "keyboard") {
        msg += "\n\n" + msg_sbmt_YN_key;
    }

    document.getElementById("submit_msg").textContent = msg;
    submitModal.showModal();
}

function submitExam() {
    localStorage.clear();
    console.log("submitting...")
    document.getElementById("examForm").submit();
    logger.log({
        mode: 'system',
        type: 'info',
        activity: 'Test Submitted',
        function_name: "submitExam()"
    });
}


document.getElementById("submit_modal_yes").addEventListener("click", () => {
    logger.log({
        mode: 'keyboard',
        type: 'command',
        activity: 'Submit Exam - yes'
    });
    submitExam()
});

document.getElementById("submit_modal_no").addEventListener("click", () => {
    logger.log({
        mode: 'keyboard',
        type: 'command',
        activity: 'Submit Exam - no'
    });

    submitModal.close();
});

function formatTime(seconds) {
    const h = Math.floor(seconds / 3600).toString().padStart(2, '0');
    const m = Math.floor((seconds % 3600) / 60).toString().padStart(2, '0');
    const s = (seconds % 60).toString().padStart(2, '0');
    return `${h}:${m}:${s}`;
}

const interval = setInterval(() => {
    remainingSeconds--;
    if (remainingSeconds <= 0) {
        clearInterval(interval);
        countdownEl.textContent = "00:00:00";
        countdownHd.textContent = "00:00:00";

        logger.log({
            mode: 'system',
            type: 'info',
            activity: 'times up ' + countdownEl.textContent
        });

        times_up = true;
        timesUpModal.showModal();
        document.getElementById("times_up_modal_yes").addEventListener("click", () => {
            submitExam();
        });
        const submitFallback = setTimeout(() => submitExam(), 5000);

        if (exam_mode == "speech") {
            if (isPlaying == true) {
                audio.pause();
                audio_wait.pause();
            }
            if (isRecording == true) {
                pauseResumeRecording();
            }
            // Guaranteed fallback — fires after 5 seconds no matter what

            Promise.resolve(speak(document.getElementById("time_up_msg").textContent))
                .catch(err => console.error("speak() failed:", err))
                .finally(() => {
                    clearTimeout(submitFallback); // Cancel fallback if speak resolved normally
                    submitExam();
                });
        }

        return; // Stop further execution in this tick
    }

    countdownEl.textContent = humanizeHMS(formatTime(remainingSeconds));
    countdownHd.textContent = formatTime(remainingSeconds);
}, 1000);

// Initialize immediately
countdownEl.textContent = formatTime(remainingSeconds);
countdownHd.textContent = formatTime(remainingSeconds);


function humanizeHMS(hms) {
    const [h, m, s] = hms.split(':').map(Number);
    const parts = [];
    if (h) parts.push(h === 1 ? '1' + ' ' + time_hr : `${h}` + ' ' + time_hrs);
    if (m) parts.push(m === 1 ? '1' + ' ' + time_min : `${m}` + ' ' + time_mins);
    if (s) parts.push(s === 1 ? '1' + ' ' + time_sec : `${s}` + ' ' + time_secs);
    if (parts.length === 0) return '0 secs';
    if (parts.length === 1) return parts[0];
    return parts.slice(0, -1).join(', ') + " " + msg_and + " " + parts.slice(-1);
}



// exam events disabling

document.getElementById('home_link').addEventListener('click', function (e) {
    e.preventDefault();
    console.log('Link disabled');
});


// Disable right-click
document.addEventListener('contextmenu', e => e.preventDefault());

// Disable common shortcuts
document.addEventListener('keydown', function (e) {
    const blocked = [
        e.ctrlKey && ['c', 'v', 'u', 's', 'a', 'p'].includes(e.key.toLowerCase()), // Copy, Paste, View Source, Save, Select All, Print
        e.ctrlKey && e.shiftKey && ['i', 'j', 'c'].includes(e.key.toLowerCase()), // DevTools
        // e.key === 'F12',         // DevTools
        e.key === 'PrintScreen', // Screenshot
        e.altKey && e.key === 'Tab', // Alt+Tab (partial)
        e.ctrlKey && e.key === 'Tab', // Tab switching in browser
    ];
    if (blocked.some(Boolean)) {
        e.preventDefault();
        violation_count += 1;
        violationCount.innerHTML = 'Blocked key combination ' + violation_count;
        logger.log({
            mode: 'system',
            type: 'violation',
            activity: 'Blocked key combination ' + violation_count
        });
    }
});


document.addEventListener('visibilitychange', function () {
    if (document.hidden) {
        violation_count += 1;
        violationCount.innerHTML = 'Tab switching detected! ' + violation_count;

        logger.log({
            mode: 'system',
            type: 'violation',
            activity: violationCount.innerHTML,
            function_name: "addEventListener('visibilitychange')"
        });
    }
});

window.addEventListener('blur', function () {
    violation_count += 1;
    violationCount.innerHTML = 'Window change detected! ' + violation_count;
    logger.log({
        mode: 'system',
        type: 'violation',
        activity: violationCount.innerHTML,
        function_name: "addEventListener('blur')"
    });


});

history.pushState(null, null, location.href);
window.addEventListener('popstate', function () {
    history.pushState(null, null, location.href);
    violation_count += 1;
    violationCount.innerHTML = 'Back button detected! ' + violation_count;
    logger.log({
        mode: 'system',
        type: 'violation',
        activity: violationCount.innerHTML,
        function_name: "addEventListener('popstate')"
    });
});