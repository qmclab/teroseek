
import re
import json
import time
from rdkit import Chem
from rdkit.Chem.Draw import rdMolDraw2D
import pandas as pd
from volcenginesdkarkruntime import Ark
from settings import *

client = Ark(
    base_url=ARK_BASE_URL,
    api_key=AEK_API_KEY,
)

def get_v3_response_json(query):
    # deepseek-v3-0324
    # 循环3次，或输出有效json
    completion = client.chat.completions.create(
        model=DS_V3_ID,
        messages=[
            {"role": "user", "content": query},
        ],
    )
    for _ in range(3):
        response = completion.choices[0].message.content
        response = response.strip().replace("`","").replace("\n","").replace("json","")
        print("get_v3_response_json result:", response)
        try:
            data = eval(response)
            return data
        except:
            continue
    return None


def get_v3_response(query):
    # deepseek-v3-0324
    # string output
    while True:
        try:
            completion = client.chat.completions.create(
                model=DS_V3_ID,
                messages=[
                    {"role": "user", "content": query},
                ],
            )
            response = completion.choices[0].message.content
            return response
        except Exception as e:
            print(f"Error occurred: {e}, retrying...")
            time.sleep(10)


def get_r1_response(query):
    # deepseek-r1-0528
    # string output
    while True:
        try:
            completion = client.chat.completions.create(
                model=DS_R1_ID,
                messages=[
                    {"role": "user", "content": query},
                ],
            )
            reasioning_content = completion.choices[0].message.reasoning_content
            content = completion.choices[0].message.content
            return reasioning_content, content
        except Exception as e:
            print(f"Error occurred: {e}, retrying...")
            time.sleep(10)


def normal_smi(smi):
    __mol = Chem.MolFromSmiles(smi)
    return Chem.MolToSmiles(__mol, canonical=True, isomericSmiles=False)


def smi_to_svg(smi, size=(150,150)):
    mol = Chem.MolFromSmiles(smi)
    drawer = rdMolDraw2D.MolDraw2DSVG(size[0], size[1])
    opts = drawer.drawOptions()
    opts.addAtomIndices = False # 禁用原子索引
    drawer.DrawMolecule(mol)
    drawer.FinishDrawing()
    svg = drawer.GetDrawingText()
    return svg


def teromol_data(tero_name, df_id_name, df_id_smi):
    matched_rows = df_id_name[
        df_id_name['mol_name'].str.contains(tero_name, case=False, regex=False, na=False)
        ].copy()
    # case = False, 忽略大小写
    # regex = False, 精确匹配，不使用正则表达式
    # na=False, 缺失值返回 false
    if matched_rows.empty:
        return None
    for row_index, row in matched_rows.iterrows():
        tkc_id = row["mol_id"]
        smi = df_id_smi[df_id_smi["mol_id"] == tkc_id]["smiles"].values[0]
        matched_rows.loc[row_index, "smi"] = normal_smi(smi)
    rows = matched_rows.drop_duplicates(subset="mol_name").drop_duplicates(subset="smi")
    data = []
    for _, row in rows.iterrows():
        mol_name = row["mol_name"]
        if len(mol_name) > 50:
            continue
        smi = row["smi"]
        data.append({
            "tkc_id": row["mol_id"],
            "mol_name": mol_name,
            "smi": smi,
            "svg": smi_to_svg(smi)
        })
    data.sort(key=lambda x: len(x["mol_name"]))
    return data


def generate_ref_html(_ref_data, ref_id):
    # ref_id = _ref_data.get("ref_id", "")
    _T_id = _ref_data.get("T_id", "")
    _doi = _ref_data.get("doi", "")
    _title = _ref_data.get("title", "")
    _year = _ref_data.get("year", "")
    _authors = _ref_data.get("authors", "")
    _publisher = _ref_data.get("publisher", "")
    _url = f"http://teroseek.qmclab.com/paper_info?T_id={_T_id}"
    ref_content = (
        f"<div class='tooltip-container'>"
        f"<a href='{_url}' target='_blank'>ref_{ref_id}: {_publisher} {_year}</a><br>"
        f"<div class='tooltip-text'>"
        f"<strong>Title:</strong> {_title}<br>"
        f"<strong>Authors:</strong> {_authors}<br>"
        f"<strong>Year:</strong> {_year}<br>"
        f"<strong>DOI:</strong> {_doi}<br>"
        f"</div></div>"
        f"<br>"
    )
    return ref_content

def generate_ref_data(_ref_data):
    _T_id = _ref_data.get("T_id", "")
    _doi = _ref_data.get("doi", "")
    _title = _ref_data.get("title", "")
    _year = _ref_data.get("year", "")
    _authors = _ref_data.get("authors", "")
    _publisher = _ref_data.get("publisher", "")
    _url = f"http://teroseek.qmclab.com/paper_info?T_id={_T_id}"
    return {
        "doi": _doi,
        "title": _title,
        "year": _year,
        "authors": _authors,
        "publisher": _publisher,
        "url": _url,
    }


def generate_mol_html(mol_name, df_id_name, df_id_smi):
    mol_name = mol_name
    mol_row = df_id_name[df_id_name["mol_name"] == mol_name]
    mol_id = mol_row["mol_id"].values[0] if not mol_row.empty else None
    mol_smi = df_id_smi[df_id_smi["mol_id"] == mol_id]["smiles"].values[0] if mol_id else ""
    mol_link = "http://terokit.qmclab.com/search.html?Chemicalname={}&database=compound".format(mol_name)
    # mol_svg = smi_to_svg(mol_smi)
    mol_content = (
        f"<div class='tooltip-container-mol'>"
        f"<a href='{mol_link}' target='_blank'>{mol_name}</a>"
        f"<div class='tooltip-text'>"
        f"<strong>Name:</strong> {mol_name}<br>"
        # f"<strong>SMILES:</strong>{mol_smi}<br>"
        f"</div></div>"
    )
    return mol_content


def generate(ref_msg_list, user_message, df_id_name, df_id_smi):
    terpene_name_list = [a.lower() for a in df_id_name["mol_name"].tolist()]
    # Send the ref_msg as the first chunk
    if ref_msg_list:
        for _ref_msg in ref_msg_list:
            time.sleep(0.05)
            yield f"data: {json.dumps({'ref_msg': _ref_msg, 'finished': False})}\n\n"
    print("生成回答，输入信息的长度为：", len(str(user_message)))
    stream = client.chat.completions.create(
        # model=DS_V3_ID,
        model = DS_R1_ID,
        messages=user_message,
        stream=True
    )
    resp_msg = ""
    for chunk in stream:
        if not chunk.choices:
            continue
        if chunk.choices[0].delta.reasoning_content:
            chunk_data = {
                'delta': chunk.choices[0].delta.reasoning_content,
                'reasoning_content': True,
                'finished': False
            }
            yield f"data: {json.dumps(chunk_data)}\n\n"
        else:
            # 为结果的流式输出添加了对萜类分子名称的链接处理，后续改写为特定的模块
            resp_msg += chunk.choices[0].delta.content
            if "\n" in chunk.choices[0].delta.content:
                # 匹配中英文括号中的内容
                matches = re.findall(r"[（(]([^）()]*)[)）]", resp_msg)
                for tero_name in matches:
                    if tero_name.lower() in terpene_name_list:
                        # print(tero_name)
                        # resp_msg = resp_msg.replace(tero_name, f'<a href="http://terokit.qmclab.com/search.html?Chemicalname={tero_name}&database=compound" target="_blank" title="terokit">{tero_name}</a>')
                        resp_msg = resp_msg.replace(tero_name, 
                                                    generate_mol_html(tero_name, df_id_name, df_id_smi))
                chunk_data = {
                    'delta': resp_msg, 
                    'reasoning_content': False,
                    'finished': False
                }
                resp_msg = ""
                yield f"data: {json.dumps(chunk_data)}\n\n"
    # 最后一次输出
    if resp_msg:
        chunk_data = {
            'delta': resp_msg, 
            'reasoning_content': False,
            'finished': True
        }
        yield f"data: {json.dumps(chunk_data)}\n\n"


def generate_guide():
    guide_info = """
    Pursuing questions about a specific piece of literature can easily amplify the AI illusion. 
    Please navigate to the detailed information of the literature for further analysis.
    """
    for _msg in guide_info:
        chunk_data = {
            'delta': _msg, 
            'reasoning_content': False,
            'finished': False
        }
        yield f"data: {json.dumps(chunk_data)}\n\n"
