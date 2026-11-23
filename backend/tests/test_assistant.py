from datetime import UTC, datetime


def test_workflow_help_turn_and_action(client, auth):
    assert client.post("/assistant/turn", json={"text": "How do I review evidence?"}).status_code == 401
    headers = auth("nurse")
    response = client.post("/assistant/turn", json={"text": "How do I review evidence?"}, headers=headers)
    assert response.status_code == 200
    initial, update = response.json()["messages"]
    assert initial["version"] == update["version"] == "v0.9.1"
    surface_id = initial["createSurface"]["surfaceId"]
    assert update["updateComponents"]["surfaceId"] == surface_id
    components = {component["id"]: component for component in update["updateComponents"]["components"]}
    assert "Compare its quote" in components["answer"]["text"]
    button = components["choose-manual"]
    assert button["id"] in components["root"]["children"]
    event = {"version": initial["version"], "action": {
        **button["action"]["event"], "surfaceId": surface_id, "sourceComponentId": button["id"],
        "timestamp": datetime.now(UTC).isoformat(),
    }}
    reply = client.post("/assistant/action", json=event, headers=headers)
    assert reply.status_code == 200
    assert "Enter from source" in reply.json()["messages"][1]["updateComponents"]["components"][1]["text"]
    event["action"]["name"] = "send_data"
    assert client.post("/assistant/action", json=event, headers=headers).status_code == 422
