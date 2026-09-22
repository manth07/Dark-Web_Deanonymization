from fastapi import APIRouter, Path, status
from app.schemas.graph import EdgeSchema, GraphResponseSchema, NodeSchema

router = APIRouter()


@router.get(
    "/mock/{target_handle}",
    response_model=GraphResponseSchema,
    status_code=status.HTTP_200_OK,
    summary="Fetch Mock Intelligence Network Graph",
    description=(
        "Generates a mock dark web relationship network graph for a target handle, "
        "including Threat Actor nodes, Crypto Wallet nodes, Server IP nodes, and connecting relationship edges."
    ),
)
async def get_mock_graph(
    target_handle: str = Path(
        ...,
        json_schema_extra={"example": "shadow_broker_99"},
        description="Target threat actor handle, username, or dark web alias",
    )
) -> GraphResponseSchema:
    """Returns a realistic mock graph structure tailored for React Flow visualizer integration."""
    actor_node_id = f"actor-{target_handle.lower()}"
    wallet_1_id = "wallet-btc-01"
    wallet_2_id = "wallet-xmr-02"
    server_ip_id = "ip-node-198-51-100-42"

    nodes = [
        NodeSchema(
            id=actor_node_id,
            label="Actor",
            name=target_handle,
            metadata={
                "threat_level": "CRITICAL",
                "known_aliases": ["shadow_op", "dark_nexus"],
                "primary_forum": "Dread",
                "risk_score": 92.5,
            },
        ),
        NodeSchema(
            id=wallet_1_id,
            label="Wallet",
            name="1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa",
            metadata={
                "blockchain": "Bitcoin (BTC)",
                "total_received_btc": 154.2,
                "transaction_count": 89,
                "first_seen": "2024-01-15T12:00:00Z",
            },
        ),
        NodeSchema(
            id=wallet_2_id,
            label="Wallet",
            name="888tW12B69z81nB67d4aB94aB32bN",
            metadata={
                "blockchain": "Monero (XMR)",
                "privacy_score": "High",
                "associated_market": "Empire Market Legacy",
            },
        ),
        NodeSchema(
            id=server_ip_id,
            label="IP",
            name="198.51.100.42",
            metadata={
                "hosting_provider": "Bulletproof Hosting Ltd",
                "country": "Germany (DE)",
                "open_ports": [22, 80, 443, 9050],
                "tor_exit_node": True,
            },
        ),
    ]

    edges = [
        EdgeSchema(
            source=actor_node_id,
            target=wallet_1_id,
            relation_type="OWNS_WALLET",
        ),
        EdgeSchema(
            source=actor_node_id,
            target=wallet_2_id,
            relation_type="OWNS_WALLET",
        ),
        EdgeSchema(
            source=actor_node_id,
            target=server_ip_id,
            relation_type="HOSTED_ON",
        ),
    ]

    return GraphResponseSchema(nodes=nodes, edges=edges)
