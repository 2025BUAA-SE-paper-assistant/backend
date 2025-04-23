def _get_prob_paper_study_question():
        payload = json.dumps(
            {
                "query": f"问题：{query}\n 回复：{ai_reply}",
                "knowledge_id": tmp_kb_id,
                "history": conversation_history[-4:],
                "prompt_name": "literature_research_assistant",
                # "max_tokens": 50,
                "temperature": 0.3,
            }
        )
        response = requests.post(file_chat_url, data=payload, headers=headers)
        question_reply = response.json().get("answer", "")
        question_reply = re.findall(r'"prediction_\d+":\s*"([^"]+)"', question_reply)
        # 取前两个结果
        question_reply = question_reply[:2]

        question_reply.append("告诉我更多")
        return question_reply