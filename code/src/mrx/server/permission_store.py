class PermissionStore:
    def __init__(self):
        self._perms: dict[str, dict[str, int]] = {}

    def update(self, subj_user_id: str, obj_user_id: str, accuracy: int):
        """on accuracy == 0, the subject loses the object as friend"""
        if subj_user_id == obj_user_id:
            print(f"WARNING (permissions): subject and object the same when updating: {subj_user_id}")
        if accuracy == 0:
            if subj_user_id in self._perms and obj_user_id in self._perms[subj_user_id]:
                del self._perms[subj_user_id][obj_user_id]
                if self._perms[subj_user_id] == {}:
                    del self._perms[subj_user_id]
                return
            else:
                print(f"WARNING (permissions): trying to remove {subj_user_id} from {obj_user_id} as friend, even though they weren't friends.")
                return
        if subj_user_id not in self._perms:
            self._perms[subj_user_id] = {}
        self._perms[subj_user_id][obj_user_id] = accuracy

    def get_perm_for_user(self, user_id: str):
        if user_id not in self._perms:
            return {}
        return self._perms[user_id]

    def get_friends(self, user_id: str):
        return self._perms[user_id]
