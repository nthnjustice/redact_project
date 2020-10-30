import os
import sys
from pathlib import Path
import asyncio
from pyppeteer import launch
import shutil
from settings import project


def redact_project(argv):
    """
    Converts python project (input) to shareable pdf project (output) with sensitive informtion redacted

    :param (list) argv: CL arguments - pass relative path to python project to convert
    :return: effect - creates [projects]/[argv[1]].zip file to share
    """

    # assign working directory
    cwd = os.getcwd()
    # assign path to python project
    input_root = os.path.join(cwd, argv[1])
    # assign path to pdf project
    output_root = os.path.join(cwd, "projects", input_root.split("/")[-1])

    # create missing directories
    Path(os.path.join(cwd, "projects")).mkdir(exist_ok=True)
    Path(output_root).mkdir(exist_ok=True)

    # loop through project directories to convert
    for dirname in project.keys():
        # assign input/output directory paths
        input_dir = os.path.join(input_root, dirname)
        output_dir = os.path.join(output_root, dirname)

        # create new output directory
        Path(output_dir).mkdir(exist_ok=True)

        # convert python scripts to html documents for directory in focus
        py_to_html(input_dir, output_dir, dirname, project[dirname]["is_public"])
        # convert html documents to pdf documents for directory in focus
        html_to_pdf(output_dir)

    # package pdf project output for sharing
    shutil.make_archive(output_root, "zip", output_root)


def py_to_html(input_dir, output_dir, dirname, is_public):
    """
    Converts python scripts to html documents so sensitive information can be redacted

    :param (str) input_dir: path to input directory with python scripts to convert
    :param (str) output_dir: path to output directory where html documents will be stored
    :param (str) dirname: name of project directory being converted
    :param (bool) is_public: if 'False' redact all python code
    """

    # assign python scripts in project directory
    scripts = get_scripts(input_dir)

    if len(scripts) == 0:
        # handle when project directory is a parent directory with child directories containing python scripts
        for subdirname in os.listdir(input_dir):
            # recurse through child directories
            input_subdir = os.path.join(input_dir, subdirname)
            output_subdir = os.path.join(output_dir, subdirname)

            Path(output_subdir).mkdir(exist_ok=True)

            py_to_html(input_subdir, output_subdir, subdirname, is_public)

    # loop through python scripts
    for script in scripts:
        # assign python code
        body = read_script(input_dir, script)

        if is_public:
            # loop through corner-cases in public directory
            for corner_case in project[dirname]["corner_cases"]:
                if corner_case["script"] == script:
                    # redact block of sensitive information in otherwise public python script
                    body = censor_code(body, corner_case["target"])
        else:
            # redact sensitive information in python script in focus
            body = censor_code(body, "def ")

        # convert and write redacted python script in focus to html document
        write_html(output_dir, script, body)


def get_scripts(input_dir):
    """
    Fetches filenames of valid python scripts in target directory

    :param (str) input_dir: path to input directory with python scripts to convert
    :return: filenames of valid python scripts in 'input_dir' argument
    """

    scripts = []

    for file in os.listdir(input_dir):
        if file.endswith(".py") and file != "__init__.py":
            scripts.append(file)

    return scripts


def read_script(input_dir, script):
    """
    Extracts code in python script as text

    :param (str) input_dir: path to input directory with python script to extract code from
    :param (str) script: filename of python script to extract code from
    :return: stringified content of 'input_dir'/'script' file
    """

    body = ""

    file = open(os.path.join(input_dir, script), "r", encoding="utf-8")

    for line in file:
        body += line

    file.close()

    return body


def censor_code(body, target):
    """
    Redacts sensitive information in python code using a rule-based system

    :param (str) body: stringified content of python code to redact
    :param (str) target: redaction rule used to match where censoring starts and ends, should be a function declaration
    :return: redacted copy of 'body' argument
    """

    # split single string representation of python code into a list of lines of code
    body = body.split("\n")
    i = 0

    # loop through each line of python code
    while i < len(body):
        # check if redaction rule is found and censoring should begin
        if target in body[i]:
            # assume function is properly documented and proceed into contents of documentation
            i += 2

            # skip contents of function documentation
            while '"""' not in body[i]:
                i += 1

            # proceed to function definition
            i += 2

            # censor all lines of the function definition until the next function declaration or end of code is found
            while "def " not in body[i]:
                line = body[i].strip()

                if line not in ["", "@staticmethod"] and line[0] != "#":
                    # censor sensitive information in function definition, ignore whitespace and comments
                    body[i] = '<span class="blur">' + body[i] + "</span>"

                # handle issue indexing beyond the number of lines of code in the entire script
                if i + 1 < len(body) and "def " not in body[i + 1]:
                    i += 1
                else:
                    break

        i += 1

    # rebuild single string representation of python code
    body = "\n".join(body)

    return body


def write_html(output_dir, script, body):
    """
    Builds, formats, and saves redacted python script as html document

    :param (str) output_dir: path to output directory where html document will be stored
    :param (str) script: filename of python script to copy name from for output html document
    :param (str) body: stringified content of redacted python code to include
    :return: effect - creates [output_dir]/[script].html file
    """

    # assign components of html document
    html_start = "<html><head><style>.blur{-webkit-filter:blur(3px)}</style></head><body><code>"
    html_end = "</code></body></html>"

    # format redacted python code for html compatibility
    body = body.replace("\n", "<br>").replace(" ", "&nbsp;").replace("<span&nbsp;", "<span ")

    # build html document
    html = html_start + body + html_end

    # save html document
    with open(os.path.join(output_dir, script[:-3] + ".html"), "w", encoding="utf-8") as file:
        file.write(html)


def html_to_pdf(output_dir):
    """
    Converts redacted html documents to pdf documents so sensitive information can't be revealed or copy-pasted

    :param (str) output_dir: path to output directory where pdf documents will be stored
    :return: effect - removes all html files in 'output_dir' directory
    """

    # assign html documents in project directory
    documents = get_documents(output_dir)

    if len(documents) == 0:
        # handle when project directory is a parent directory with child directories containing html documents
        for subdirname in os.listdir(output_dir):
            # recurse through child directories
            output_subdir = os.path.join(output_dir, subdirname)
            html_to_pdf(output_subdir)

    # loop through html documents
    for document in documents:
        # convert redacted html document in focus into secure pdf document
        asyncio.get_event_loop().run_until_complete(write_pdf(output_dir, document))
        # remove copy of html document in focus
        os.remove(os.path.join(output_dir, document))


def get_documents(output_dir):
    """
    Fetches filenames of redacted html documents in target directory

    :param (str) output_dir: path to output directory with html documents to convert
    :return: filenames of redacted html documents in 'output_dir' argument
    """

    return [document for document in os.listdir(output_dir) if document.endswith(".html")]


async def write_pdf(output_dir, document):
    """
    Launches headless Chrome instance to open redacted html document and convert it to a pdf document

    :param (str) output_dir: path to output directory where html document will be read and pdf document saved
    :param (str) document: filename of html document to open and to copy name from for output pdf document
    :return: effect - creates [output_dir]/[document].pdf file
    """

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
