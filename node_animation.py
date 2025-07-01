import numpy as np
from manim import *
import random
import math

class NodeAvatar(VGroup):
    def __init__(self, position, avatar_type="face", **kwargs):
        super().__init__(**kwargs)
        self.position = position
        self.avatar_type = avatar_type
        self.rotation_speed = random.uniform(-0.1, 0.1)
        
        # Create the main node circle
        self.main_circle = Circle(
            radius=0.4,
            color=random.choice([BLUE, RED, GREEN, YELLOW, PURPLE, ORANGE]),
            fill_opacity=0.8,
            stroke_width=3
        ).move_to(position)
        
        # Create avatar features
        self.create_avatar()
        
        # Create glow effect
        self.glow = Circle(
            radius=0.6,
            color=self.main_circle.color,
            fill_opacity=0.2,
            stroke_opacity=0.4
        ).move_to(position)
        
        # Add all elements to the group
        self.add(self.glow, self.main_circle, self.avatar)
        
    def create_avatar(self):
        """Create a beautiful avatar inside the node"""
        self.avatar = VGroup()
        
        if self.avatar_type == "face":
            # Eyes
            left_eye = Dot(radius=0.05, color=BLACK).shift(LEFT * 0.15 + UP * 0.1)
            right_eye = Dot(radius=0.05, color=BLACK).shift(RIGHT * 0.15 + UP * 0.1)
            
            # Mouth (smile)
            mouth = Arc(
                radius=0.15,
                start_angle=-PI/3,
                angle=2*PI/3,
                color=BLACK,
                stroke_width=3
            ).shift(DOWN * 0.05)
            
            self.avatar.add(left_eye, right_eye, mouth)
            
        elif self.avatar_type == "star":
            star = Star(n=5, outer_radius=0.2, color=WHITE, fill_opacity=0.8)
            self.avatar.add(star)
            
        elif self.avatar_type == "tech":
            # Create tech-like avatar
            screen = Rectangle(width=0.25, height=0.15, color=BLUE, fill_opacity=0.7)
            lines = VGroup(*[
                Line(LEFT * 0.1, RIGHT * 0.1).shift(UP * (0.05 - i * 0.03))
                for i in range(3)
            ]).set_color(WHITE).scale(0.5)
            self.avatar.add(screen, lines)
        
        self.avatar.move_to(self.position)

class BrilliantNodeAnimation(Scene):
    def construct(self):
        # Set background
        self.camera.background_color = "#000011"
        
        # Create title
        title = Text("Brilliant Node Avatar Animation", font_size=48, gradient=[BLUE, PURPLE])
        title.to_edge(UP)
        
        # Create nodes in formation
        self.nodes = self.create_node_network()
        
        # Animation sequence
        self.play(
            FadeIn(title),
            *[FadeIn(node) for node in self.nodes],
            run_time=2
        )
        
        self.wait(1)
        
        # Animation 1: Spinning Head Avatars
        self.animate_spinning_heads()
        
        # Animation 2: Explosive Expansion
        self.animate_expansion()
        
        # Animation 3: Merge into Glowing Singularity
        self.animate_merge_singularity()
        
        # Animation 4: Approach Center
        self.animate_approach_center()
        
        # Final showcase
        self.final_showcase()
        
    def create_node_network(self):
        """Create initial network of nodes"""
        positions = [
            [-4, 2], [0, 2], [4, 2],
            [-2, 0], [2, 0],
            [-4, -2], [0, -2], [4, -2]
        ]
        
        avatar_types = ["face", "star", "tech"] * 3
        nodes = []
        
        for i, pos in enumerate(positions):
            node = NodeAvatar(
                np.array([pos[0], pos[1], 0]),
                avatar_type=avatar_types[i % 3]
            )
            nodes.append(node)
            
        return nodes
    
    def animate_spinning_heads(self):
        """Animation 1: Spinning head avatars with orbital motion"""
        subtitle = Text("1. Spinning Head Avatars", font_size=36, color=YELLOW)
        subtitle.to_edge(DOWN)
        
        self.play(FadeIn(subtitle))
        
        # Create spinning and orbital animations
        animations = []
        for i, node in enumerate(self.nodes):
            # Spinning animation
            spin_anim = Rotate(node.avatar, angle=4*PI, run_time=4)
            
            # Orbital motion around original position
            orbit_center = node.get_center()
            orbit_radius = 0.5
            orbit_path = Circle(radius=orbit_radius).move_to(orbit_center)
            orbital_anim = MoveAlongPath(node, orbit_path, run_time=4)
            
            animations.extend([spin_anim, orbital_anim])
        
        self.play(*animations)
        self.play(FadeOut(subtitle))
        
        # Reset positions
        reset_anims = []
        for i, node in enumerate(self.nodes):
            original_pos = np.array([
                [-4, 2], [0, 2], [4, 2],
                [-2, 0], [2, 0],
                [-4, -2], [0, -2], [4, -2]
            ][i] + [0])
            reset_anims.append(node.animate.move_to(original_pos))
        
        self.play(*reset_anims, run_time=1)
        
    def animate_expansion(self):
        """Animation 2: Explosive expansion outward"""
        subtitle = Text("2. Explosive Expansion", font_size=36, color=ORANGE)
        subtitle.to_edge(DOWN)
        
        self.play(FadeIn(subtitle))
        
        # Calculate expansion vectors
        center = ORIGIN
        expansion_animations = []
        
        for node in self.nodes:
            current_pos = node.get_center()
            direction = current_pos - center
            # Normalize and scale
            if np.linalg.norm(direction) > 0:
                direction = direction / np.linalg.norm(direction)
            
            # Explosive expansion
            expanded_pos = center + direction * 6
            
            # Create particle effect
            particles = VGroup(*[
                Dot(radius=0.02, color=node.main_circle.color)
                for _ in range(20)
            ])
            for particle in particles:
                particle.move_to(current_pos)
                
            # Animate expansion with particles
            expansion_animations.extend([
                node.animate.move_to(expanded_pos).scale(1.5),
                *[
                    particle.animate.move_to(
                        expanded_pos + np.random.uniform(-2, 2, 3)
                    ).set_opacity(0)
                    for particle in particles
                ]
            ])
            
            self.add(particles)
        
        self.play(*expansion_animations, run_time=3)
        self.play(FadeOut(subtitle))
        
    def animate_merge_singularity(self):
        """Animation 3: Merge into glowing singularity"""
        subtitle = Text("3. Merge into Glowing Singularity", font_size=36, color=PURPLE)
        subtitle.to_edge(DOWN)
        
        self.play(FadeIn(subtitle))
        
        # Create central singularity
        singularity = Circle(
            radius=0.1,
            color=WHITE,
            fill_opacity=1.0,
            stroke_width=0
        ).move_to(ORIGIN)
        
        # Create intense glow rings
        glow_rings = VGroup(*[
            Circle(
                radius=0.2 + i * 0.3,
                color=PURPLE,
                fill_opacity=0.1 / (i + 1),
                stroke_opacity=0.3 / (i + 1)
            ).move_to(ORIGIN)
            for i in range(5)
        ])
        
        self.add(singularity, glow_rings)
        
        # Animate nodes merging into center
        merge_animations = []
        for node in self.nodes:
            # Scale down while moving to center
            merge_animations.extend([
                node.animate.move_to(ORIGIN).scale(0.1).set_opacity(0.3),
            ])
        
        # Pulse the singularity
        singularity_pulse = singularity.animate.scale(3).set_opacity(0.8)
        glow_pulse = glow_rings.animate.scale(2)
        
        self.play(*merge_animations, run_time=2)
        self.play(singularity_pulse, glow_pulse, run_time=1)
        
        # Explosive release
        self.play(
            singularity.animate.scale(10).set_opacity(0),
            glow_rings.animate.scale(5).set_opacity(0),
            run_time=1.5
        )
        
        self.play(FadeOut(subtitle))
        
        # Reset and recreate nodes
        self.remove(*self.nodes)
        self.nodes = self.create_node_network()
        self.add(*self.nodes)
        
    def animate_approach_center(self):
        """Animation 4: Approach center with swirling motion"""
        subtitle = Text("4. Approach Center", font_size=36, color=GREEN)
        subtitle.to_edge(DOWN)
        
        self.play(FadeIn(subtitle))
        
        # Create swirling paths to center
        approach_animations = []
        
        for i, node in enumerate(self.nodes):
            # Create spiral path
            start_pos = node.get_center()
            
            # Parametric spiral function
            def spiral_func(t):
                radius = np.linalg.norm(start_pos) * (1 - t)
                angle = np.arctan2(start_pos[1], start_pos[0]) + 4 * PI * t
                return np.array([
                    radius * np.cos(angle),
                    radius * np.sin(angle),
                    0
                ])
            
            spiral_path = ParametricFunction(
                spiral_func,
                t_range=[0, 1],
                color=node.main_circle.color
            )
            
            # Add trail effect
            self.add(spiral_path)
            
            approach_animations.append(
                MoveAlongPath(node, spiral_path, run_time=4)
            )
        
        self.play(*approach_animations)
        self.play(FadeOut(subtitle))
        
    def final_showcase(self):
        """Final beautiful showcase"""
        finale_text = Text("Manim: Professional Animation Quality", 
                          font_size=36, 
                          gradient=[BLUE, PURPLE, PINK])
        finale_text.to_edge(DOWN)
        
        # Create beautiful final formation
        final_animations = []
        
        # Arrange nodes in a perfect circle
        for i, node in enumerate(self.nodes):
            angle = i * 2 * PI / len(self.nodes)
            final_pos = 2.5 * np.array([np.cos(angle), np.sin(angle), 0])
            
            final_animations.extend([
                node.animate.move_to(final_pos).scale(1.2),
                node.glow.animate.set_opacity(0.8)
            ])
        
        # Add connecting lines
        connection_lines = VGroup()
        for i in range(len(self.nodes)):
            for j in range(i + 1, len(self.nodes)):
                line = Line(
                    self.nodes[i].get_center(),
                    self.nodes[j].get_center(),
                    color=BLUE,
                    stroke_opacity=0.3
                )
                connection_lines.add(line)
        
        self.play(
            *final_animations,
            FadeIn(finale_text),
            Create(connection_lines),
            run_time=3
        )
        
        # Final rotation of the entire network
        network = VGroup(*self.nodes, connection_lines)
        self.play(
            Rotate(network, angle=2*PI, run_time=4),
            finale_text.animate.set_color(GOLD)
        )
        
        self.wait(2)

# To render the animation, save this as a .py file and run:
# manim -pql your_file.py BrilliantNodeAnimation

if __name__ == "__main__":
    print("🎬 Professional Node Animation with Manim")
    print("=" * 50)
    print("To render this animation:")
    print("1. Install Manim: pip install manim")
    print("2. Save this code as 'node_animation.py'")
    print("3. Run: manim -pql node_animation.py BrilliantNodeAnimation")
    print()
    print("Quality options:")
    print("  -pql  : Preview quality (480p)")
    print("  -pqm  : Medium quality (720p)")
    print("  -pqh  : High quality (1080p)")
    print("  -pqk  : 4K quality (2160p)")
    print("=" * 50)
    print()
    print("Features implemented:")
    print("✅ Spinning head avatars with orbital motion")
    print("✅ Explosive expansion with particle effects")
    print("✅ Merge into glowing singularity")
    print("✅ Approach center with spiral motion")
    print("✅ Professional-grade smooth animations")
    print("✅ Beautiful lighting and glow effects")
    print("✅ Multiple avatar types (face, star, tech)")
    print("✅ Cinema-quality rendering")