from datetime import date, timedelta


def test_planner_create_overlap_complete_and_delete(api_client):
    registration = api_client.post("/api/v1/auth/register", json={
        "email": "planner@example.com", "password": "A-secure-pass-123", "full_name": "Planner Learner",
    })
    headers = {"Authorization": f"Bearer {registration.json()['access_token']}"}
    tomorrow = (date.today() + timedelta(days=1)).isoformat()
    payload = {
        "title": "Quant practice", "subject": "Quantitative aptitude", "study_date": tomorrow,
        "start_time": "09:00", "end_time": "10:00",
    }

    created = api_client.post("/api/v1/planner", headers=headers, json=payload)
    overlapping = api_client.post("/api/v1/planner", headers=headers, json={**payload, "start_time": "09:30", "end_time": "10:30"})
    listing = api_client.get(f"/api/v1/planner?start_date={tomorrow}&end_date={tomorrow}", headers=headers)
    completed = api_client.patch(f"/api/v1/planner/{created.json()['id']}", headers=headers, json={"completed": True})
    deleted = api_client.delete(f"/api/v1/planner/{created.json()['id']}", headers=headers)
    after_delete = api_client.get(f"/api/v1/planner?start_date={tomorrow}&end_date={tomorrow}", headers=headers)

    assert created.status_code == 201
    assert overlapping.status_code == 409
    assert len(listing.json()) == 1
    assert completed.json()["completed"] is True
    assert deleted.status_code == 204
    assert after_delete.json() == []
