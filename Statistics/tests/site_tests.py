# состояние страниц
def test_url():

    result = client.get("/")

    print(result.status_code)
    assert result.status_code == 200
