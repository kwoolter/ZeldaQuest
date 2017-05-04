__author__ = 'JaneW'

import csv
import logging
'''
This module contains some framework classes for creating maps:-
    - Location - basic description of a location
    - LocationFactory - abstract factory class for storing Locations
    - MapLink - a class to define how two locations are linked together
    - LevelMap - defines a map by storing the MapLinks between all locations in the map
    - MapFactory - abstract factory class for creating LevelMaps
'''


class MapLink:
    '''
    MapLink - A link between two locations
    The link represents:
     - a "from" location ID
     - a "to" location ID
     - the direction of travel to get between from/to locations
     - an optional description of how you get from/to
     - an optional flag to indicate if the link is locked somehow
     - an optional description of why the link is locked
     - an optional flag for suppressing creation of the reverse map link i.e. for a one-way link
    '''

    # What directions are valid and what is their reverse equivalent
    valid_directions = ["NORTH", "SOUTH", "EAST", "WEST", "UP", "DOWN"]
    valid_reverse_directions = ["SOUTH", "NORTH", "WEST", "EAST", "DOWN", "UP"]
    valid_flags = {"TRUE": True, "FALSE": False}

    LOCKED = 0
    UNLOCKED = 1
    HIDDEN = 999
    UNHIDDEN = 1000
    HIDDEN_STAT = "Hidden"

    # Constructor
    def __init__(self, from_id, to_id, direction, description=None, \
                 is_lockable: bool = False, locked: bool = False, locked_description: str = None, \
                 reversible: bool = True, hidden: bool = False):

        self.from_id = from_id
        self.to_id = to_id
        self.description = description
        self.direction = direction
        self.locked = locked
        self.is_lockable = is_lockable
        self.locked_description = locked_description
        self.reversible = reversible
        self.hidden = hidden

        # If the direction supplied is not valid then log an error
        if direction not in MapLink.valid_directions:
            logging.warning((str(self) + ": Direction " + direction + " is not valid."))

    # Return a MapLink object that is the reverse of this one
    def get_reverse_link(self):
        return MapLink(self.to_id, self.from_id, self.get_reverse_direction(self.direction), self.description, \
                       is_lockable=self.is_lockable, locked=self.locked, \
                       locked_description=self.locked_description, reversible=self.reversible)

    # Given a valid direction look-up its reverse
    def get_reverse_direction(self, direction):
        i = MapLink.valid_directions.index(direction)
        return MapLink.valid_reverse_directions[i]

    # Check to see if this MapLink is valid
    def is_valid(self):
        return self.direction in MapLink.valid_directions

    # Check if the link is locked
    def is_locked(self):
        # If this link is not lockable then locked is always false
        if self.is_lockable == False:
            locked = False
        # If no game state provided then use local state
        else:
            locked = self.locked
        return locked

    # lock/unlock a link
    def lock(self, is_locked : bool = True):

        self.locked = is_locked


    # Check if the link is hidden
    def is_hidden(self):

        return self.is_hidden

    # hide/unhide a link
    def hide(self, is_hidden : bool = True):

        self.hidden = is_hidden

    # Convert the MapLink object to a string
    def __str__(self):
        link_description = "Go " + self.direction + " from " + str(
            self.from_id) + " " + self.description + " to " + str(self.to_id) + "."
        if self.is_locked() == True and self.locked_description != None:
            link_description += self.locked_description
        if self.is_hidden() == True:
            link_description += "(Hidden)"
        return link_description

class LevelMap:
    '''
    The LevelMap class holds the details of how all of the locations in the map link together
    The map is stored as a dictionary that for each location ID stores the list of available MapLinks
    These MapLinks represent all of the directions that you can travel in from that location
    '''

    # Constructor
    def __init__(self, level, name):

        self.level = level
        self.name = name
        self._locations = None

        # A map to store the list of links for each location ID in the map
        self.mapLinks = {}

    # Add a new link to the map and also add the reverse link
    # e.g. if you can go East from 1 to 2, you can go West from 2 to 1
    def add_link(self, new_link):

        # First see if the link that you are trying to add is valid?
        if (new_link.is_valid() == False):
            logging.warning("Trying to add invalid link: " + str(new_link))
            return

        # See if there is already a list of links for the "from" location
        if new_link.from_id in self.mapLinks:
            list_links = self.mapLinks[new_link.from_id]
        # If not create a new blank list
        else:
            list_links = []

        # add the new link to the list
        list_links.append(new_link)

        # and store it back in the map of location IDs to links
        self.mapLinks[new_link.from_id] = list_links

        # add the reverse link as well if the link is reversible
        if new_link.reversible == True:
            # See if there is already a list of links for the "to" location
            if new_link.to_id in self.mapLinks:
                list_links = self.mapLinks[new_link.to_id]
            # If not create a new blank list
            else:
                list_links = []

            # add the reverse of the new link to the list
            list_links.append(new_link.get_reverse_link())

            # and store it back in the map of locations to links
            self.mapLinks[new_link.to_id] = list_links

    # Get the list of links for a specified location in the map
    def get_location_links(self, location_id):
        return self.mapLinks.get(location_id)

    # Get the map of links for a specified location in the map keyed by direction
    def get_location_links_map(self, location_id):
        link_map = {}
        for link in self.get_location_links(location_id):
            link_map[link.direction] = link
        return link_map

    # lock/unlock the specified link and its reverse link
    def lock(self, location_id, direction, is_locked):

        # get the map of links for the specified location
        link_map = self.get_location_links_map(location_id)

        # if specified direction has a link...
        if (direction in link_map.keys()):

            # get the link and lock/unlock it
            selected_link = link_map[direction]
            selected_link.lock(is_locked)

            # find out what the reverse link looks like
            reverse_link = selected_link.get_reverse_link()

            # loop through all of the links from the 'to' location
            for selected in self.mapLinks[selected_link.to_id]:

                # if we find the link that is the reverse then lock/unlock it
                if selected.to_id == location_id and selected.direction == reverse_link.direction:
                    selected.lock(is_locked)

        # else the specified link could not be found to lock it
        else:
            logging.warning(
                "Lock(" + str(is_locked) + "): No link found " + direction + " from location " + str(location_id))

    # Print out all of the locations in the Level Map
    def print(self):

        output_width = 60

        print("\n\n")
        print((" Welcome to Level " + str(self.level) + " : " + self.name + " ").center(output_width, "-"))

        # For each of the location IDs in the map...
        for location_links in self.mapLinks.values():
            for link in location_links:
                print(str(link))


'''
A factory class to load in level maps and store them
'''


class MapFactory(object):
    def __init__(self):

        # A dictionary of level ID to LevelMap
        self._maps = {}

    def load(self, map_name: str, map_level: int, map_file_name: str):

        # Create a map of level and add it to the Factory
        new_map = LevelMap(map_level, map_name)
        self._maps[new_map.level] = new_map

        logging.info("%s.load(): Loading new map %s from '%s'.", __class__, new_map.name, map_file_name)

        # Attempt to open the map file
        with open(map_file_name, 'r') as data_file:

            # Load all rows in as a dictionary
            reader = csv.DictReader(data_file)

            # Get the list of column headers
            header = reader.fieldnames

            # For each row in the file....
            for row in reader:

                from_loc_id = int(row.get("FromID"))
                to_loc_id = int(row.get("ToID"))
                direction = row.get("Direction").upper()

                if direction not in MapLink.valid_directions:
                    logging.error("%s.load(): %s not a valid direction.", __class__, direction)
                    break

                description = row.get("Description")

                is_lockable = row.get("Lockable").upper()
                if is_lockable in MapLink.valid_flags.keys():
                    is_lockable = MapLink.valid_flags[is_lockable]
                elif is_lockable == "":
                    is_lockable = False
                else:
                    logging.warning("%s.load(): Lockable flag '%s' for location %i to %i not recognised", \
                                    __class__, is_lockable, from_loc_id, to_loc_id)
                    is_lockable = False

                locked = row.get("Locked").upper()
                if locked in MapLink.valid_flags.keys():
                    is_locked = MapLink.valid_flags[locked]
                elif locked == "":
                    is_locked = False
                else:
                    logging.warning("%s.load(): Locked flag %s not recognised", __class__, locked)
                    is_locked = False

                locked_description = row.get("LockedDescription")

                reversible = row.get("Reversible").upper()
                if reversible in MapLink.valid_flags.keys():
                    is_reversible = MapLink.valid_flags[reversible]
                elif reversible == "":
                    is_reversible = True
                else:
                    logging.warning("%s.load(): Reversible flag %s not recognised", __class__, reversible)
                    is_reversible = False

                hidden = row.get("Hidden").upper()
                if hidden in MapLink.valid_flags.keys():
                    is_hidden = MapLink.valid_flags[hidden]
                elif hidden == "":
                    is_hidden = False
                else:
                    logging.warning("%s.load(): Hidden flag %s not recognised", __class__, hidden)
                    is_hidden = False

                new_map_link = MapLink(from_loc_id, to_loc_id, direction, description, \
                                       is_lockable, is_locked, locked_description, is_reversible, is_hidden)

                logging.info("%s.load(): Loaded map link From %i %s to %i", \
                             __class__, new_map_link.from_id, new_map_link.direction, new_map_link.to_id)

                new_map.add_link(new_map_link)

    # Return the LevelMap with the specified ID
    def get_map(self, id):
        return self._maps[id]
