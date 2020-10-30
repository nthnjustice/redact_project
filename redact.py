import os
import sys
from pathlib import Path
import asyncio
from pyppeteer import launch
import shutil
from settings import project


def redact_project(argv):
    cwd = os.getcwd()
    input_root = os.path.join(cwd, argv[1])
    output_root = os.path.join(cwd, "projects", input_root.split("/")[-1])

    Path(os.path.join(cwd, "projects")).mkdir(exist_ok=True)
    Path(output_root).mkdir(exist_ok=True)

    for dirname in project.keys():
        input_dir = os.path.join(input_root, dirname)
        output_dir = os.path.join(output_root, dirname)

        Path(output_dir).mkdir(exist_ok=True)

        py_to_html(input_dir, output_dir, dirname, project[dirname]["status"])
        html_to_pdf(output_dir)

    shutil.make_archive(output_root, "zip", output_root)


def py_to_html(input_dir, output_dir, dirname, status):
    scripts = get_scripts(input_dir)

    if len(scripts) == 0:
        for subdirname in os.listdir(input_dir):
            input_subdir = os.path.join(input_dir, subdirname)
            output_subdir = os.path.join(output_dir, subdirname)

            Path(output_subdir).mkdir(exist_ok=True)

            py_to_html(input_subdir, output_subdir, subdirname, status)

    for script in scripts:
        body = read_script(input_dir, script)

        if status == "public":
            for corner_case in project[dirname]["corner_cases"]:
                if corner_case["script"] == script:
                    body = censor_code(body, corner_case["target"])
        elif status == "private":
            body = censor_code(body, "def ")

        write_html(output_dir, script, body)


def get_scripts(input_dir):
    scripts = []

    for file in os.listdir(input_dir):
        if file.endswith(".py") and file != "__init.py":
            scripts.append(file)

    return scripts


def read_script(input_dir, script):
    body = ""

    file = open(os.path.join(input_dir, script), "r", encoding="utf-8")

    for line in file:
        body += line

    file.close()

    return body


def censor_code(body, target):
    body = body.split("\n")
    i = 0

    while i < len(body):
        if target in body[i]:
            i += 2

            while '"""' not in body[i]:
                i += 1

            i += 2

            while "def " not in body[i]:
                line = body[i].strip()

                if line not in ["", "@staticmethod"] and line[0] != "#":
                    body[i] = '<span class="blur">' + body[i] + "</span>"

                if i + 1 < len(body) and "def " not in body[i + 1]:
                    i += 1
                else:
                    break

        i += 1

    body = "\n".join(body)

    return body


def write_html(output_dir, script, body):
    html_start = "<html><head><style>.blur{-webkit-filter:blur(3px)}</style></head><body><code>"
    html_end = "</code></body></html>"

    body = body.replace("\n", "<br>").replace(" ", "&nbsp;").replace("<span&nbsp;", "<span ")

    html = html_start + body + html_end

    with open(os.path.join(output_dir, script[:-3] + ".html"), "w", encoding="utf-8") as file:
        file.write(html)


def html_to_pdf(output_dir):
    documents = get_documents(output_dir)

    if len(documents) == 0:
        for subdirname in os.listdir(output_dir):
            output_subdir = os.path.join(output_dir, subdirname)
            html_to_pdf(output_subdir)

    for document in documents:
        asyncio.get_event_loop().run_until_complete(write_pdf(output_dir, document))
        os.remove(os.path.join(output_dir, document))


def get_documents(output_dir):
    return [document for document in os.listdir(output_dir) if document.endswith(".html")]


async def write_pdf(output_dir, document):
    options = {
        "path": os.path.join(output_dir, document[:-5] + ".pdf"),
        "landscape": True
    }

    browser = await launch()
    page = await browser.newPage()
    await page.goto(os.path.join("file:///", output_dir, document))
    options["width"] = await page.evaluate("() => document.documentElement.offsetHeight")
    await page.pdf(options)
    await browser.close()


if __name__ == "__main__":
    redact_project(sys.argv)
