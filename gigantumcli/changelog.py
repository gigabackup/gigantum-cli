import requests


class ChangeLog(object):
    """Class to provide an interface to the posted ChangeLog information"""

    def __init__(self):
        """Constructor"""
        # Load data
        self._change_log_url = "https://s3.amazonaws.com/io.gigantum.changelog/changelog.json"
        self.data = self._load_data()

    def _load_data(self):
        """Load the changelog data file from remote source

        Returns:
            dict
        """
        data = None
        try:
            response = requests.get(self._change_log_url)
            data = response.json()
        finally:
            return data

    def is_update_available(self, tag):
        """Method to check if an update is available using the changelog as a history

        Args:
            tag(str): The 8-char short hash tag for the CURRENT image in used

        Returns:
            bool
        """
        latest_image_id = self.data['latest']['id']
        return latest_image_id != tag

    def latest_tag(self):
        """Method to get the latest tag from the changelog data

        Returns:
            str
        """
        latest_image_id = self.data['latest']['id']
        tag = None
        for t in self.data:
            if t == "latest":
                continue

            if self.data[t]['id'] == latest_image_id:
                tag = t
                break

        if not tag:
            raise ValueError("Failed to look up latest image tag.")

        return tag

    def get_changelog(self, tag="latest"):
        """Method to print the changelog data

        Args:
            tag(str): Version of the changelog to grab

        Returns:
            str
        """
        if not self.data:
            # No changelog data was available...probably no internet connection
            return None

        if tag not in self.data:
            raise ValueError("Tag {} not available".format(tag))

        data = self.data[tag]
        msg = "Version: {}\n".format(data['id'])
        msg = "{}Release Date: {}\n".format(msg, data['date'])
        msg = "{}Note: \n".format(msg)

        # Show notices
        if 'messages' in data:
            for note in data['messages']:
                msg = "{}  - {}\n".format(msg, note)

        # Show changes
        for change_key in data['changes']:
            msg = "{}\n{}: \n".format(msg, change_key)
            for change_str in data['changes'][change_key]:
                msg = "{}  - {}\n".format(msg, change_str)

        return msg

