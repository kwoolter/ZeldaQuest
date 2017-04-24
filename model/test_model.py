import model
import logging

def main():

    new_floor = model.Floor(name = "floor1", rect = (0,0,1000,100))

    new_player = model.Player(name = "keith", rect = (10,10,20,20))
    new_floor.add_player(new_player)

    new_player = model.Player(name="jack", rect=(10, 10, 20, 20))
    new_floor.add_player(new_player)

    new_player = model.Player(name="rosie", rect=(100, 100, 20, 20))
    new_floor.add_player(new_player)

    new_object = model.RPGObject(name="crate", rect=(90,90,10,10))
    new_floor.add_object(new_object)


    for player1 in new_floor.players.values():

        player_collision = new_floor.is_player_collide(player1)
        touched = new_floor.is_object_touching(player1)

        print("Player {0}: collision={1}, touching={2}".format(player1.name, player_collision, touched))



    selected_player = new_floor.players["jack"]
    selected_player.move(50,50)
    for player1 in new_floor.players.values():
        player_collision = new_floor.is_player_collide(player1)
        touched = new_floor.is_object_touching(player1)

        print("Player {0}: collision={1}, touching={2}".format(player1.name, player_collision, touched))


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()



