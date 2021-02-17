import os
import random

import cherrypy

"""
This is a simple Battlesnake server written in Python.
For instructions see https://github.com/BattlesnakeOfficial/starter-snake-python/README.md
"""


class Battlesnake(object):
    @cherrypy.expose
    @cherrypy.tools.json_out()
    def index(self):
        # This function is called when you register your Battlesnake on play.battlesnake.com
        # It controls your Battlesnake appearance and author permissions.
        # TIP: If you open your Battlesnake URL in browser you should see this data
        return {
            "apiversion": "1",
            "author": "Fibonachos",  # TODO: Your Battlesnake Username
            "color": "#888888",  # TODO: Personalize
            "head": "default",  # TODO: Personalize
            "tail": "default",  # TODO: Personalize
        }

    @cherrypy.expose
    @cherrypy.tools.json_in()
    def start(self):
        # This function is called everytime your snake is entered into a game.
        # cherrypy.request.json contains information about the game that's about to be played.
        data = cherrypy.request.json

        print("START")
        return "ok"

    @cherrypy.expose
    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    def move(self):
        # This function is called on every turn of a game. It's how your snake decides where to move.
        # Valid moves are "up", "down", "left", or "right".
        # TODO: Use the information in cherrypy.request.json to decide your next move.
        data = cherrypy.request.json

   
        you = data["you"]
        head = you["head"]
        body = you["body"]

        
        board = data["board"].copy()

        #determine which board spaces are occupied by snakes
        snake_bodies = []
        snake_heads = []
        snakes = board["snakes"].copy()

        for snake in snakes:
          snake_bodies += snake["body"]
          if snake["head"] != head:
            snake_heads.append(snake["head"])


        #all the square the other snakes might move are also hazards (unless you are bigger than them)
        head_hazards = []
        for enemy_head in snake_heads:
          #up
          danger = enemy_head.copy()
          danger["y"] += 1
          head_hazards.append(danger)

          #down
          danger = enemy_head.copy()
          danger["y"] -= 1
          head_hazards.append(danger)

          #left
          danger = enemy_head.copy() 
          danger["x"] += 1
          head_hazards.append(danger)

          #right
          danger = enemy_head.copy() 
          danger["x"] -= 1
          head_hazards.append(danger)

        #determine where the nearest food is, so can hunt it down
        food = board['food']

        #this function returns the distance of the nearest food
        def nearby_food(food,head):
          nearest_food_dist = 1000
          for bite in food:
            distance = abs(head["x"]-bite["x"])+abs(head["y"]-bite["y"])
            if distance < nearest_food_dist:
              nearest_food = bite.copy()
              nearest_food_dist = distance
          return nearest_food_dist

        #the distance of the nearest food to the head
        base_food = nearby_food(food,head)
        
        #this function determines where the proposed head will be if move is made
        def proposed_head(head,move):
          p_h = head.copy()
          if move == "up":
            p_h["y"] += 1
            #print("goin up!")
          if move == "down":
            p_h["y"] -= 1
            #print("goin down!")
          if move == "right":
            p_h["x"] += 1
            #print("goin right!")
          if move == "left":
            p_h["x"] -= 1
            #print("goin left!")
          return p_h

        #The snake move reward program
        go_up = 0
        go_down = 0
        go_left = 0
        go_right = 0

        #determines whether a proposed move will make the snake crash
        def crash_test(hazards,p_h):
          return p_h["x"] < 0 or p_h["x"] >= 11 or p_h["y"] < 0 or p_h["y"] >= 11 or p_h in hazards

        #define hazard zones relative to edges
        green = [3,4,5,6,7]
        yellow = [1,2,8,9]
        red = [0,10]
        
        edge_weight = 1
        food_weight = 1
        crash_weight = 100
        head_weight = 50
        # hazards: snake_bodies, head_hazards, edges
        ##################################
        ## pros and cons of going right ##
        ##################################

        p_h = proposed_head(head,"right")

        #crashing into snakes and walls is obviously a big no no
        if crash_test(snake_bodies,p_h):
          go_right -= crash_weight 

        #going where you might collide with the head of another snake is bad, but not
        # as bad as crashing into a wall or body
        if crash_test(head_hazards,p_h):
          go_right -= head_weight

         #penalty for going towards edges where might get pinned
        if p_h["x"] in yellow:
          go_right -= edge_weight
        if p_h["y"] in yellow:
          go_right -= edge_weight
        if p_h["x"] in red:
          go_right -= 2*edge_weight
        if p_h["y"] in red:
          go_right -= 2*edge_weight

        #for now we want it to go towards the nearest food  
        go_right += base_food - nearby_food(food,p_h)
        
        
        
        ##################################
        ## pros and cons of going left ##
        ##################################
        p_h = proposed_head(head,"left")

        #crashing is obviously a big no no
        if crash_test(snake_bodies,p_h):
          go_left -= crash_weight  

        #going where you might collide with the head of another snake is bad, but not
        # as bad as crashing into a wall or body
        if crash_test(head_hazards,p_h):
          go_left -= head_weight 

        #penalty for going towards edges where might get pinned
        if p_h["x"] in yellow:
          go_left -= edge_weight
        if p_h["y"] in yellow:
          go_left -= edge_weight
        if p_h["x"] in red:
          go_left -= 2*edge_weight
        if p_h["y"] in red:
          go_left -= 2*edge_weight

        #for now we want it to go towards the nearest food  
        go_left += base_food - nearby_food(food,p_h)

        
        
        ##################################
        ## pros and cons of going up ##
        ##################################
        p_h = proposed_head(head,"up")

        #crashing is obviously a big no no
        if crash_test(snake_bodies,p_h):
          go_up -= crash_weight 

        #going where you might collide with the head of another snake is bad, but not
        # as bad as crashing into a wall or body
        if crash_test(head_hazards,p_h):
          go_up -= head_weight 

        #penalty for going towards edges where might get pinned
        if p_h["x"] in yellow:
          go_up -= edge_weight
        if p_h["y"] in yellow:
          go_up -= edge_weight
        if p_h["x"] in red:
          go_up -= 2*edge_weight
        if p_h["y"] in red:
          go_up -= 2*edge_weight

        #for now we want it to go towards the nearest food  
        go_up += base_food - nearby_food(food,p_h)

        
        
        ##################################
        ## pros and cons of going down ###
        ##################################
        p_h = proposed_head(head,"down")

        #crashing is obviously a big no no
        if crash_test(snake_bodies,p_h):
          go_down -= crash_weight 

        #penalty for going towards edges where might get pinned
        if p_h["x"] in yellow:
          go_down -= edge_weight
        if p_h["y"] in yellow:
          go_down -= edge_weight
        if p_h["x"] in red:
          go_down -= 2*edge_weight
        if p_h["y"] in red:
          go_down -= 2*edge_weight

        #going where you might collide with the head of another snake is bad, but not
        # as bad as crashing into a wall or body
        if crash_test(head_hazards,p_h):
          go_down -= head_weight 

        #for now we want it to go towards the nearest food  
        go_left += base_food - nearby_food(food,p_h)




        #determine which moves are the most benificial
        options = {'down':go_down,'left':go_left,'right':go_right,'up':go_up}
        max_value = max(options.values())
        best_moves = [k for k,v in options.items() if v == max_value]

        #pick a move randomly between best moves
        move = random.choice(best_moves)

        print(f"MOVE: {move}")
        return {"move": move}

    @cherrypy.expose
    @cherrypy.tools.json_in()
    def end(self):
        # This function is called when a game your snake was in ends.
        # It's purely for informational purposes, you don't have to make any decisions here.
        data = cherrypy.request.json

        print("END")
        return "ok"


if __name__ == "__main__":
    server = Battlesnake()
    cherrypy.config.update({"server.socket_host": "0.0.0.0"})
    cherrypy.config.update(
        {"server.socket_port": int(os.environ.get("PORT", "8080")),}
    )
    print("Starting Battlesnake Server...")
    cherrypy.quickstart(server)
