class PendingRequestStore:
    def __init__(self):
        self._pending: set[str] = set()

    def add_pending(self, user_id: str):
        self._pending.add(user_id)

    def remove_pending(self, user_id: str):
        if user_id not in self._pending:
            print(f"WARNING: trying to remove user {user_id} from pending, even though they don't have a request pending.")
            return
        self._pending.remove(user_id)

    def get_requests_to_send(self, online_users: set[str]):
        return self._pending.intersection(online_users)