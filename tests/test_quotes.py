import pytest

from bark.projects.models import Quote
from bark.projects.schemas import QuoteStatus


class TestSellerBarks:
    base_url = "/seller/barks"

    @pytest.fixture(autouse=True)
    def setup(self, client, db):
        from bark.projects.models import Project

        self.client = client
        self.db = db
        project = Project(
            id=1,
            response_cap=5,
            response_count=0,
            project_title="Web dev",
            buyer_user_id=2,
        )
        db.add(project)
        db.commit()

    def test_create_quote(self, client):
        project_id = 1
        response = client.post(
            f"{self.base_url}/{project_id}/quotes",
            json={"seller_id": 10, "message": "I can help!", "price_cents": 5000},
        )

        assert response.status_code == 200
        assert response.json()["seller_id"] == 10
        assert response.json()["price_cents"] == 5000

    def test_duplicate_seller_quote_returns_400(self, client):
        project_id = 1
        first_response = client.post(
            f"{self.base_url}/{project_id}/quotes",
            json={"seller_id": 10, "message": "I can help!", "price_cents": 5000},
        )

        assert first_response.status_code == 200

        second_response = client.post(
            f"{self.base_url}/{project_id}/quotes",
            json={"seller_id": 10, "message": "I can help again!", "price_cents": 4500},
        )

        assert second_response.status_code == 400
        assert (
            second_response.json()["detail"]
            == "Seller already has a quote for this bark"
        )

    def test_create_quote_on_bark_with_5_quotes_should_fail_with_bad_input(
        self, client, db
    ):
        from bark.projects.models import Project

        project = Project(
            id=2,
            response_cap=5,
            response_count=5,
            project_title="Another web dev",
            buyer_user_id=2,
        )
        db.add(project)
        db.commit()

        project_id = 2
        response = client.post(
            f"{self.base_url}/{project_id}/quotes",
            json={
                "seller_id": 10,
                "message": "I swear I can help!",
                "price_cents": 5000,
            },
        )

        assert response.status_code == 400
        assert response.json()["detail"] == "Bark already reach max response cap"


class TestBuyerProjects:
    base_url = "/buyer/projects"

    def test_accept_quote_on_bark_and_verify_rejects_others(self, client, db):
        from bark.projects.models import Project

        project = Project(
            id=3,
            response_cap=5,
            response_count=1,
            project_title="Web dev",
            buyer_user_id=2,
        )
        db.add(project)
        quote_to_accept_id = 1
        quote_to_accept = Quote(
            id=quote_to_accept_id,
            seller_id=1,
            message="I can help!",
            price_cents=2000,
            project_id=project.id,
        )
        db.add(quote_to_accept)
        quote_to_reject_id = 2
        quote_to_reject = Quote(
            id=quote_to_reject_id,
            seller_id=2,
            message="I can also help!",
            price_cents=3000,
            project_id=project.id,
        )
        db.add(quote_to_reject)
        db.commit()

        response = client.post(
            f"{self.base_url}/{project.id}/quotes/{quote_to_accept_id}/accept",
        )

        assert response.status_code == 200
        assert response.json()["status"] == "accepted"
        assert response.json() == {
            "id": 1,
            "project_id": 3,
            "seller_id": 1,
            "message": "I can help!",
            "price_cents": 2000,
            "status": "accepted",
        }
        db.refresh(quote_to_reject)
        assert quote_to_reject.status == QuoteStatus.rejected
