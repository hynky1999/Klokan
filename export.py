# %%
from html import unescape
import os
from unicodedata import normalize
import json


def export(file, export_dir):
    with open(file, "r") as f:
        text = f.read()
        text = unescape(text)
        text = normalize("NFKC", text)
    rows = text.split("\n")
    year = int(file.split("_")[-1].split(".")[0])
    print(f"Processing year {year}")

    # %%
    pos_to_row = {}
    cumulative_pos = 0
    for i,row in enumerate(rows):
        pos_to_row[cumulative_pos] = i
        cumulative_pos += len(row) + 1

    # %%
    # Find all rows that start with number.

    import re
    result = [(m.group(1), m.start()) for m in re.finditer(r"\n(\d+\..*)", text)]
    # Now for each row, we need to know its row number.
    # We can do that by creating a mapping from row number to position in text.


    # %%
    # Take only results with at least 40 characters.
    result = [r for r in result if len(r[0]) > 40]

    # %%
    def get_question(row_i, max_rows=5):
        """
        Function iterates over rows until it find an empty row or row with (A)
        If we don't find end by max_rows, we return None
        """

        for i in range(row_i, row_i + max_rows):
            if not rows[i] or rows[i].startswith('(A)'):
                # Get index of the question
                question = ' '.join(rows[row_i:i])
                index, question = question.split('.', 1)
                return {
                    'index': int(index),
                    'question': question.strip(),
                    'start_row': row_i,
                    'end_row': i,
                }
        return None


    questions = [get_question(pos_to_row[r[1] + 1]) for r in result]
    questions = [q for q in questions if q is not None]

    # %%
    len(questions)

    # %%
    # Filter out black list of words.
    # We have to make sure that question doesn't refer to images
    black_list = [
        "obráz",
        "obraz",
        "koul",
        "kruh",
        "čtver",
        "trojúheln",
        "hranol",
        "nakresl",
        "obdel",
        "znač"
    ]
    filtered_out_questions = [q for q in questions if any(b in q["question"] for b in black_list)]
    questions = [q for q in questions if not any(b in q["question"] for b in black_list)]

    # %%
    len(questions)

    # %%

    def convert_to_answer_pair(answer):
        """
        Function takes answer which is expected to be in format
        (Letter) Answer
        and returns tuple (Letter, Answer)

        The letter is expected to be in range A-E
        """
        match = re.match(r'\(([A-E])\)', answer)
        if match is None:
            return None
        
        end_of_letter = match.end()
        letter = match.group(1)
        answer = answer[end_of_letter:].strip()
        return letter, answer



    def get_answers(start, max_rows=15):
        """
        Function iterates over rows until and must find all 5 answers.
        Each answer is denoted with (A), (B), (C), (D), (E).
        Answer is valid until either:
            1. Next answer is found
            2. New line is found

        If we don't find all answers by max_rows, we return None
        """
        answers = []
        text = '\n'.join(rows[start:start + max_rows])
        matches = re.findall(r'(\((A|B|C|D|E)\)[^\(\n]+)', text)
        answers = [m[0] for m in matches]
        answer_pairs = [convert_to_answer_pair(a) for a in answers]
        answer_pairs = [a for a in answer_pairs if a is not None]
        # Now for each letter get the answer that appears first.
        final_answers = {
        }
        for letter in ['A', 'B', 'C', 'D', 'E']:
            for a in answer_pairs:
                if a[0] == letter:
                    final_answers[letter] = a[1]
                    break

        if len(final_answers) == 5:
            return final_answers
        return None

    # %%
    # Now for each question, we need to find its answers.
    # If we don't find answers, we discard the question.

    questions_with_answers = []
    for q in questions:
        answers = get_answers(q["end_row"])
        if answers is not None:
            questions_with_answers.append({
                'question': q,
                'answers': answers
            })
    len(questions_with_answers)

    # %%
    # Now group questions to series of increasing indexes.
    def group_questions(qas):
        """
        Function takes dictionar of questions and answers and groups them
        based on question index. Each group must have increasing indexes.
        """

        groups = []
        current_group = []
        for qa in qas:
            q = qa['question']
            if len(current_group) == 0:
                current_group.append(qa)
                continue
            if q['index'] > current_group[-1]['question']['index']:
                current_group.append(qa)
            else:
                groups.append(current_group)
                current_group = [qa]
        groups.append(current_group)
        return groups

    qa_groups = group_questions(questions_with_answers)

    # Now create a blocks of question_naswers which have consecutive numbers.
    anchor_text_dict = (
        (2004, 'správná řešenı́ soutěžnı́ch úloh'),
        (2005, 'správná řešení soutěžních úloh'),
        (2007, 'výsledky jednotlivých kategorií'),
        (2011, 'správná řešení soutěžních úloh'),
    )


    def get_results(start_row, max_rows=800):
        """
        Each results starts with: výsledky jednotlivých kategorií
        Then there is name of the category and then there is results
        in format: Number Letter, Number Letter, ...
        """

        search_text = '\n'.join(rows[start_row:start_row + max_rows])
        # Itterate from right to left until you find a number than is lower or equal to year
        # Then you have found the anchor text.
        anchor_text = ""
        for pos_anchor in anchor_text_dict[::-1]:
            if pos_anchor[0] <= year:
                anchor_text = pos_anchor[1]
                break





        results_start = re.search(anchor_text.lower(), search_text.lower())
        # print(search_text)
        if results_start is None:
            print('Didn\'t find anchor')
            return None
        
        # After that you should search for results in format:
        # Number Letter, Number Letter, ... this can span multiple lines.
        results_search_text = search_text[results_start.end():]
        # Remove all lines with following pattern:
        # Úlohy za \d body\ů:
        results_search_text = re.sub(r'Úlohy za \d+ bod(y|ů):?', '', results_search_text)

        results = re.search(r'(\d+(\s|\n)*[A-E])((\n|,)(\s|\n)*\d+\s*[A-E])*', results_search_text, re.MULTILINE)
        if results is None:
            print('No results found')
            return None
        # Lastly parse the result into a dictionary.
        results = results.group(0)
        # We will use regex instead

        results = re.findall(r'(\d+)\s*([A-E])', results)
        results = {int(r[0]): r[1] for r in results}
        return results



    results = [
        get_results(qa_group[-1]['question']['end_row']) for qa_group in qa_groups
    ] 
    results = [r for r in results if r is not None]
    # Check that each result values are unique.
    for i,r1 in enumerate(results):
        for r2 in results[i+1:]:
            if set(r1.values()).intersection(set(r2.values())) == min(len(r1), len(r2)):
                raise Exception('Results are not unique')
            

            


    # %%
    def merge_into_dataset(qa_groups, results):
        """
        Function takes qa_groups and results and merges them into a single dataset.
        """
        assert len(qa_groups) == len(results)
        dataset = []
        for i, (qa_group, result) in enumerate(zip(qa_groups, results)):
            for qa in qa_group:
                try:
                    dataset.append({
                        'question': qa['question']['question'],
                        'answers': qa['answers'],
                        'correct_answer': result[qa['question']['index']],
                        'category': i,
                        'year': year,
                    })
                except KeyError:
                    print('Question {} of {}not found in results'.format(qa['question']['index'],i))
        return dataset


    dataset = merge_into_dataset(qa_groups, results)
    return dataset

    # %%




datasets = []
for file in os.listdir("text"):
    if file.endswith('.txt'):
        datasets += [export(os.path.join("text", file), "exported")]
    
dataset = [d for ds in datasets for d in ds]
print('Total questions: {}'.format(len(dataset)))
with open('dataset.json', 'w') as f:
    json.dump(dataset, f, indent=2, ensure_ascii=False)
