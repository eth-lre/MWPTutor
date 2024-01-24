import { DEVMODE } from './globals'

let SERVER_DATA_ROOT = DEVMODE ? "http://127.0.0.1:9001/queues/" : "queues/"
let SERVER_LOG_ROOT = DEVMODE ? "http://127.0.0.1:5000/" : "https://zouharvi.pythonanywhere.com/"

export async function load_data(): Promise<any> {
    let random_v = `?v=${Math.random()}`;
    let result :string = await $.ajax(
        SERVER_DATA_ROOT + globalThis.uid + ".jsonl" + random_v,
        {
            type: 'GET',
            contentType: 'application/text',
        }
    )
    result = result.trimEnd()
    // @ts-ignore
    result = "[" + result.replaceAll("\n", ",") + "]"
    result = JSON.parse(result)
    return result
}

export async function log_data(data_i: number): Promise<any> {
    let data = {
        "data_i": data_i,
        "answer": globalThis.data_log[data_i]["answer"],
        "sid": globalThis.data[data_i]["sid"],
        "sentence": globalThis.data[data_i]["sentence"],
        "time": {
            "start": globalThis.time_start,
            "end": Date.now(),
        },
        "uid": globalThis.uid,
        "user": {
            "prolific_pid": globalThis.prolific_pid,
            "session_id": globalThis.session_id,
            "study_id": globalThis.study_id,
        },
    }

    console.log(data)

    let result = await $.ajax(
        SERVER_LOG_ROOT + "log",
        {
            data: JSON.stringify({
                project: "evaluating-dialogue-quality",
                uid: globalThis.uid,
                payload: JSON.stringify(data),
            }),
            type: 'POST',
            contentType: 'application/json',
        }
    )
    return result
}

export async function get_json(name: string): Promise<Array<object>> {
    let result = await $.ajax(
        name,
        {
            type: 'GET',
            contentType: 'application/text',
        }
    )
    result = result.trimEnd()
    // @ts-ignore
    result = "[" + result.replaceAll("\n", ",") + "]"
    result = JSON.parse(result)
    return result
}

export async function get_html(name: string): Promise<string> {
    return await $.ajax(
        name,
        {
            type: 'GET',
            contentType: 'text/html',
        }
    )
}