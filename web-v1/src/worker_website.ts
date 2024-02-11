import { log_data, get_json, get_html } from "./connector";
import { DEVMODE } from "./globals";
import { timer } from "./utils";

let main_text_area = $("#main_text_area")

export async function setup_intro_information_1() {
    // hide for now
    $("#side_panel").toggle(false)

    main_text_area.html(await get_html(`instructions_1_${globalThis.stimulus_type}.html`))
    await timer(10)
    $("#button_start").on("click", () => {
        $("#side_panel").toggle(true)
    
        if (globalThis.stimulus_type == "prompt") {
            $("#short_instructions_prompt").toggle(true)
            $("#short_instructions_hint").toggle(false)
        } else if (globalThis.stimulus_type == "hint") {
            $("#short_instructions_prompt").toggle(false)
            $("#short_instructions_hint").toggle(true)
        }
        setup_navigator();
    })
}

let finished_questions = new Set<number>()

export async function setup_main_question(data_i: number) {
    let data_now = globalThis.data[data_i];
    globalThis.time_start = Date.now()
    let html = await get_html("main_task.html")
    let styled_utterance = (
        "<b class='spaker_span'>Question:</b>" + data_now["question"] + "<br><br>")  +
    (
        data_now["context"]
        .replace(/\n\n/g, "<br class='utterance_break'>")
        .replace(/\nEOM\n/g, "<br class='utterance_break'>")
        .replace(/Tutor:/g, "<b class='speaker_span'>Tutor:</b> ")
        .replace(/Student:/g, "<b class='speaker_span'>Student:</b> ")
    ) + (
        "<br><br><span class='highlight_span'><b class='speaker_span'>Tutor:</b> " + 
        data_now["current_utterance"] + "</span>"
    ) + (
        "<br><br><b>Current step:</b> " + 
        data_now["solution_step"] + "</span>"
    )
    html = html.replace("{{SENTENCE}}", styled_utterance)


    let check_brighten_navigator_button = () => {
        let is_finished = Object.keys(globalThis.data_log[data_i]["answer"]).length == 4
        $(`#navigator_button_${data_i}`).toggleClass(
            "navigator_button_finished",
            is_finished
        )
        if (is_finished) {
            finished_questions.add(data_i)
            if (finished_questions.size == globalThis.data.length) {
                $("#finish_study").removeAttr("disabled")
            }
        } else {
            $("#finish_study").attr("disabled", "disabled")
            if (finished_questions.has(data_i)) {
                finished_questions.delete(data_i)
            }
        }
    }

    let html_buttons = ""

    function setup_button_hook_static(id_name: string, label_name: string) {
        let extra_class_no = ""
        let extra_class_yes = ""
        if (globalThis.data_log[data_i]["answer"].hasOwnProperty(id_name)) {
            if(globalThis.data_log[data_i]["answer"][id_name]) {
                extra_class_yes = "button_selected"
            } else {
                extra_class_no = "button_selected"
            }
        }
        html_buttons += `<span class="label_span">${label_name}:</span> `
        html_buttons += `<input type="button" id_val="${id_name}" value="Yes" id="${id_name}_yes" class="button_yes ${extra_class_yes}"> `
        html_buttons += `<input type="button" id_val="${id_name}" value="No" id="${id_name}_no" class="button_no ${extra_class_no}"> `
        html_buttons += "\n"
    }

    if (globalThis.stimulus_type == "prompt") {
        setup_button_hook_static("grammatical", "Grammatical")
        setup_button_hook_static("relevant", "Relevant")
        html_buttons += "<br>"
        setup_button_hook_static("redundant", "Not redundant")
        setup_button_hook_static("not_reveal", "Does not reveal answer")
    } else if (globalThis.stimulus_type == "hint") {
        setup_button_hook_static("grammatical", "Grammatical")
        setup_button_hook_static("specific", "Specific")
        html_buttons += "<br>"
        setup_button_hook_static("helpful", "Helpful")
        setup_button_hook_static("not_reveal", "Does not reveal answer")
    }

    html = html.replace("{{BUTTONS_SECTION}}", html_buttons)

    main_text_area.html(html)
    await timer(10)

    $(".button_yes").each((index, element) => {
        let el_button = $(element);
        let id_val = el_button.attr("id_val") as string;
        el_button.on("click", () => {
            el_button.addClass("button_selected");
            $(`#${id_val}_no`).removeClass("button_selected");
            globalThis.data_log[data_i]["answer"][id_val] = true
            check_brighten_navigator_button()
            log_data(data_i)
        })
    })
    $(".button_no").each((index, element) => {
        let el_button = $(element);
        let id_val = el_button.attr("id_val") as string;
        el_button.on("click", () => {
            el_button.addClass("button_selected");
            $(`#${id_val}_yes`).removeClass("button_selected");
            globalThis.data_log[data_i]["answer"][id_val] = false
            check_brighten_navigator_button()
            log_data(data_i)
        })
    })
}

export async function setup_navigator() {
    globalThis.data_log = {}
    globalThis.data.forEach((element, element_i) => {
        globalThis.data_log[element_i] = {"question": element["question"], "answer": {}}
    })
    let buttons = globalThis.data.map((element, element_i) => {
        return `<input type="button" class="navigator_button" value="${element_i+1}" id="navigator_button_${element_i}">`
    }).join("\n");
    $("#progress_window").html(
        buttons + "\n\n" +
        $("#progress_window").html()
    )
    await timer(10)
    $(".navigator_button").on("click", (event) => {
        let element = $(event.target);
        let target_i = Number.parseInt(element.val() as string) -1;
        setup_main_question(target_i);
    })

    setup_main_question(0)

    $("#finish_study").on("click", load_thankyou)
}

async function load_thankyou() {
    $("#side_panel").toggle(false)
    main_text_area.html("Please wait 3s for data synchronization to finish.")
    await timer(1000)
    main_text_area.html("Please wait 2s for data synchronization to finish.")
    await timer(1000)
    main_text_area.html("Please wait 1s for data synchronization to finish.")
    await timer(1000)

    let html_text = `Thank you for participating in our study. For any further questions about this project or your data, <a href="mailto:vilem.zouhar@inf.ethz.ch">send us a message</a>.`;
    html_text += `<br>Please click <a class="button_like" href="https://app.prolific.com/submissions/complete?cc=CFEUE41O">this link</a> to go back to Prolific. `
    html_text += `Alternatively use this code <em>CFEUE41O</em>.`
    main_text_area.html(html_text);
}