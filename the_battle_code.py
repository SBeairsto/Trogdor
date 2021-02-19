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

        #############################
        ##  Function Definitions   ##
        #############################   
        
        #this function returns the distance of the nearest food
        def nearby_food(food,head):
          nearest_food_dist = 1000
          for bite in food:
            distance = abs(head["x"]-bite["x"])+abs(head["y"]-bite["y"])
            if distance < nearest_food_dist:
              nearest_food_dist = distance
          return nearest_food_dist

        
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

      
        #this function determines all the ajacent squares to a given square
        def adjacent_squares(square):
          
          adj_squares = []
          
          #up
          temp = square.copy()
          temp["y"] += 1
          adj_squares.append(temp)

          #down
          temp = square.copy()
          temp["y"] -= 1
          adj_squares.append(temp)

          #left
          temp = square.copy() 
          temp["x"] += 1
          adj_squares.append(temp)

          #right
          temp = square.copy() 
          temp["x"] -= 1
          adj_squares.append(temp)

          return adj_squares   


        #determines whether a proposed move will make the snake crash into
        #a wall or the given hazards 
        def crash_test(hazards,p_h):
          return p_h["x"] < 0 or p_h["x"] >= 11 or p_h["y"] < 0 or p_h["y"] >= 11 or p_h in hazards

        ###################################################
        ##  Pull board information and define variables  ##
        ###################################################
        
        my_snake = data["you"].copy()
        my_head = my_snake["head"].copy()
        my_body = my_snake["body"].copy()

        board = data["board"].copy()
        food = board['food']
        all_snakes = board["snakes"].copy()


        #determine which board spaces are occupied by the bodies
        #and heads of other snakes
        other_bodies = []
        other_heads = []
        
        for snake in all_snakes:
          if not snake["body"] in my_body: 
            other_bodies += snake["body"]
          if snake["head"] != my_head:
            other_heads.append(snake["head"])        

        #determines all the squares the other snake heads might move in the next
        #turn. (Attack these if we are bigger than them, avoid otherwise)
        around_other_heads = []
        for enemy_head in other_heads:
          around_other_heads.append(adjacent_squares(enemy_head))
       
         #determines all the squares around the bodies of other snakes (might
         #want to avoid these as it is possible to get trapped by them)
        around_other_bodies = []
        for part in other_bodies:
          around_other_bodies.append(adjacent_squares(part))

        #determines all the squares around the bodies of our snake (might
        #want to avoid these as it is possible to get trapped by them)
        around_my_body = []
        for part in my_body:
          around_my_body.append(adjacent_squares(part))          

        #the distance of the nearest food to our head
        base_food = nearby_food(food,my_head)
        

        ####################################
        ## The snake move reward program ##
        ####################################
        
        go_up = 0
        go_down = 0
        go_left = 0
        go_right = 0

        #define hazard zones relative to edges
        green = [3,4,5,6,7]  #safest near the middle
        yellow = [1,2,8,9]  #bit more dangerous towards the edges
        red = [0,10] #can easily get pinned right on edges and corners

        #define weights of rewards and penalties, tweak these for best performance
        
        #reward for avoiding edges
        edge_weight = 2

        #reward for moving towards nearest food
        if my_snake["health"] < 30:
          food_weight = 1
        else:
          food_weight = 1

        #penalty for crashing into wall or body
        crash_weight = 100
      
        #penalty for moving to squares adjacent to enemy heads
        head_weight = 50

        #penalty for moving within a square of snake bodies
        body_weight = 6
        

        ##################################
        ## pros and cons of going right ##
        ##################################
        p_h = proposed_head(my_head,"right")

        #crashing into snakes and walls is obviously a big no no
        if crash_test(other_bodies,p_h):
          go_right -= crash_weight  
        if crash_test(my_body,p_h):
          go_right -= crash_weight  

        #going where you might collide with the head of another snake is bad, but not
        # as bad as crashing into a wall or body
        go_right -= head_weight*around_other_heads.count(p_h)

        #we are going to try to keep a buffer between our head and bodies
        go_right -= body_weight*around_other_bodies.count(p_h) 

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
        go_right += (base_food - nearby_food(food,p_h))*food_weight
        
        
        ##################################
        ## pros and cons of going left ##
        ##################################
        p_h = proposed_head(my_head,"right")

        #crashing into snakes and walls is obviously a big no no
        if crash_test(other_bodies,p_h):
          go_left -= crash_weight  
        if crash_test(my_body,p_h):
          go_left -= crash_weight  

        #going where you might collide with the head of another snake is bad, but not
        # as bad as crashing into a wall or body
        go_left -= head_weight*around_other_heads.count(p_h)

        #we are going to try to keep a buffer between our head and bodies
        go_left -= body_weight*around_other_bodies.count(p_h) 

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
        go_left += (base_food - nearby_food(food,p_h))*food_weight

        
        
        ##################################
        ## pros and cons of going up ##
        ##################################
        p_h = proposed_head(my_head,"right")

        #crashing into snakes and walls is obviously a big no no
        if crash_test(other_bodies,p_h):
          go_up -= crash_weight  
        if crash_test(my_body,p_h):
          go_up -= crash_weight  

        #going where you might collide with the head of another snake is bad, but not
        # as bad as crashing into a wall or body
        go_up -= head_weight*around_other_heads.count(p_h)

        #we are going to try to keep a buffer between our head and bodies
        go_up -= body_weight*around_other_bodies.count(p_h) 

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
        go_up += (base_food - nearby_food(food,p_h))*food_weight

        
        
        ##################################
        ## pros and cons of going down ###
        ##################################
        p_h = proposed_head(my_head,"right")

        #crashing into snakes and walls is obviously a big no no
        if crash_test(other_bodies,p_h):
          go_down -= crash_weight  

        if crash_test(my_body,p_h):
          go_down -= crash_weight   

        #going where you might collide with the head of another snake is bad, but not
        # as bad as crashing into a wall or body
        go_down -= head_weight*around_other_heads.count(p_h)

        #we are going to try to keep a buffer between our head and bodies
        go_down -= body_weight*around_other_bodies.count(p_h) 

        #penalty for going towards edges where might get pinned
        if p_h["x"] in yellow:
          go_down -= edge_weight
        if p_h["y"] in yellow:
          go_down -= edge_weight
        if p_h["x"] in red:
          go_down -= 2*edge_weight
        if p_h["y"] in red:
          go_down -= 2*edge_weight

        #for now we want it to go towards the nearest food  
        go_down += (base_food - nearby_food(food,p_h))*food_weight





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
