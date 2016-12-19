from __future__ import print_function
import cv2,re,numpy as np,random,math,time,thread,decimal,tkMessageBox,matplotlib,os
from pprint import pprint
from Tkinter import *
matplotlib.use('TkAgg')
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2TkAgg
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib import rcParams
from PIL import Image, ImageTk


'''
class data_preprocessor_handler:

	def image_dir_to_matrix_txt(self, dirname):
		new_txt_file = open(dirname+".txt", "a")
		image_file_names = os.listdir(dirname)
		for image_file_name in image_file_names:
		 	if(image_file_name[0:1] != "."):
		 		print(image_file_name)

'''


class matrix_data_loader_handler:

	def __init__(self, matrix_dims, to_retreive, file_name,user_interface):
		self.user_interface = user_interface
		self.matrix_width = matrix_dims[0]
		self.matrix_height = matrix_dims[1]
		self.to_retreive = to_retreive
		self.file_name = file_name
		self.user_interface.print_console("Loading "+str(self.to_retreive)+" items from " + self.file_name + "... \n")
		self.data_set = open(file_name, 'r').read().split(",")
		self.matrices = []
		self.targets = []
		self.input_divider_val = 255.0

	def populate_matrices(self):
		px_count = 0
		done_msg = "Finished loading data \n "
		for i in range(self.to_retreive):
			if(self.user_interface.cancel_training == True):
				done_msg = "**CANCELLED** \n "
				break
			matrix = np.zeros((self.matrix_width,self.matrix_height), dtype=np.float32)
			for px_col in range(self.matrix_width):
				for px_row in range(self.matrix_height):
					if(px_count%((self.matrix_width*self.matrix_height))==0):
						self.targets.append(int(self.data_set[px_count]))
					else:
						matrix[px_col][px_row] = float(self.data_set[px_count]) / self.input_divider_val
					px_count += 1
			if(i%(int(self.to_retreive/5))==0):
				self.user_interface.print_console("Loaded "+str(i)+"/"+str(self.to_retreive))
			self.matrices.append(matrix)

		self.user_interface.print_console(done_msg)

	def prep_matrix_for_input(self, matrix):
		matrix_float = matrix.astype(np.float32)
		matrix_for_input = matrix_float / float(self.input_divider_val)
		return matrix_for_input



class user_interface_handler:

	frame_height = 800
	frame_width = 1200

	def __init__(self, tk_main):
		self.tk_main = tk_main
		self.ui_frame = Frame(self.tk_main)
		self.ui_frame.pack()
		self.tk_main.title("BrainBuilder By Caspar Wylie") 
		self.tk_main.minsize(width=self.frame_width, height=self.frame_height)
 		self.tk_main.maxsize(width=self.frame_width, height=self.frame_height)
 		self.font_face = "Helvetica"
 		self.main_font_size = 13
 		self.tk_main.protocol('WM_DELETE_WINDOW', self.tk_main.quit)
 		self.canvas_height = 500
		self.canvas_width = 950
		self.cancel_training = False
		self.new_line_count = 0
		self.canvas_labels = []
		self.render_ui_frames()
		self.render_ui_widgets()
		self.can_clear_graph = False

	def render_ui_frames(self):

		self.learn_options_frame = Frame(self.ui_frame,width=500)
 		self.learn_options_frame.pack(fill=BOTH,side=LEFT)
 		#self.console_frame = Frame(self.ui_frame,bg="grey",height=300,width=400)
 		#self.console_frame.pack()
 		self.c_scrollbar = Scrollbar(self.tk_main)
		self.c_scrollbar.pack(side=RIGHT, fill=Y)

		self.lower_frame = Frame(self.ui_frame)
		self.lower_frame.pack(side=BOTTOM, fill=BOTH)
 		self.console_list_box = Text(self.lower_frame,bg="grey",height=19,width=34,borderwidth=0, highlightthickness=0,font=("courier bold", 10))
 		self.console_list_box.pack(padx=3,ipady=20,ipadx=10,side=LEFT,fill=Y)
 		self.console_list_box.config(yscrollcommand=self.c_scrollbar.set)
 		self.console_list_box.configure(state="disabled")
 		self.c_scrollbar.config(command=self.console_list_box.yview)
 		self.tk_nn_visual_canvas = Canvas(self.ui_frame, width=self.canvas_width, height=self.canvas_height,background="grey")
		self.tk_nn_visual_canvas.pack(side=RIGHT)

		self.g_figures = range(2)
		self.g_axis = range(2)
		self.g_lines = [[],[]]
		self.g_canvas = range(2)

		rcParams.update({'figure.autolayout': True})

		self.line_colors = ["blue","green","red","magneta","cyan","yellow"]
		self.render_graph("% Of Error (from 1000 feedforwards)","1000 forward feeds","%",0,"r")
		self.render_graph("% Of Success (from test data each Epoch)","Epoch","%",1,"b")
		self.prepare_new_line_graph()

	def render_graph(self,title,xlabel,ylabel,line_num,col):

		self.g_figures[line_num] =  plt.figure()
		self.g_axis[line_num] = self.g_figures[line_num].add_subplot(111)
		self.g_axis[line_num].set_ylabel(ylabel)
		self.g_axis[line_num].set_xlabel(xlabel)
		self.g_figures[line_num].suptitle(title)
		self.g_axis[line_num].get_yaxis().set_visible(False)
		self.g_axis[line_num].get_xaxis().set_visible(False)
		self.g_canvas[line_num] = FigureCanvasTkAgg(self.g_figures[line_num], master=self.lower_frame)
		self.g_canvas[line_num].get_tk_widget().config(width=360,height=280)
		self.g_canvas[line_num].get_tk_widget().pack(side=LEFT,fill=X)

	prev_line_1_data = 0.0
	axis_g_showing = [False,False]
	all_g1_annotations = []
	def animate_graph_figures(self, line,data):
		if(self.axis_g_showing[line]==False):
			self.g_axis[line].get_yaxis().set_visible(True)
			self.g_axis[line].get_xaxis().set_visible(True)
			self.axis_g_showing[line]=True
			
		ydata = self.g_lines[line][-1].get_ydata()
		ydata = np.append(ydata,data)
		#print(ydata)
		self.g_lines[line][-1].set_ydata(ydata)
		self.g_lines[line][-1].set_xdata(range(len(ydata)))
		self.g_axis[line].relim()
		self.g_axis[line].autoscale_view()

		if(line==1): 
			if(data!=self.prev_line_1_data):
				self.all_g1_annotations.append(self.g_axis[line].annotate(str(data)+"%",(len(ydata)-1,data)))
				self.all_g1_annotations[-1].set_fontsize(9)
			self.prev_line_1_data = data

		self.g_figures[line].canvas.draw()

	def clear_graphs(self):
		if(self.can_clear_graph==True):
			for ann in range(len(self.all_g1_annotations)):
				self.all_g1_annotations[ann].remove()
			self.all_g1_annotations = []
			for i in range(2):
				pprint(self.g_lines)
				for line in range(len(self.g_lines[i])):
					self.g_lines[i][line].remove()
				self.g_lines[i] = []
				self.g_figures[i].canvas.draw()
			self.new_line_count = 0
			self.can_clear_graph = False
			self.prepare_new_line_graph()

	def prepare_new_line_graph(self):
		for line in range(2):
			new_line, = self.g_axis[line].plot([], [], self.line_colors[self.new_line_count][0:1]+"-")
			self.g_lines[line].append(new_line)
		self.new_line_count += 1

 	def render_ui_widgets(self):

 		default_hidden_layers_str = "50"
 		default_bias_str = "0,0"
 		default_input_dims = "28,28"
 		default_output_count = "10"
	 	input_text_length = 8

 		def render_option(text, command,parent_frame,side=None,anchor=None):
 			option = Button(parent_frame, text=text, command=command)
 			option.pack(side=side,anchor=anchor)
 			return option

 		def render_nn_vis_trigger(event=None):
 			if(event==None):
 				hidden_str = default_hidden_layers_str
 				bias_str = default_bias_str
 				input_dims = default_input_dims
 				output_count = int(default_output_count)
 			else:
 				hidden_str = self.hidden_layer_input_label.get()
 				bias_str = self.bias_vals_input_label.get()
 				input_dims = self.matrix_dim_input_label.get()
 				output_count_str = self.output_count_input_label.get()
 				if(output_count_str.isdigit()):
 					output_count = int(output_count_str)
 				else:
 					output_count = -1

 			if(self.check_str_list_valid(hidden_str+bias_str) == True and hidden_str != "" and bias_str != "" and input_dims != ""):
 				if(hidden_str[-1]==","):
 					hidden_str = hidden_str[0:-1]
 				if(bias_str[-1]==","):
 					bias_str = bias_str[0:-1]
 				if(input_dims[-1]==","):
 					input_dims = input_dims[0:-1]
 				if(self.check_str_list_valid(input_dims) == True and output_count > 0):
 					input_dims = input_dims.split(",")

 					inputs_total = int(input_dims[0])
 					if(len(input_dims)==2): inputs_total = inputs_total * int(input_dims[1])
	 				layers = [inputs_total]
		 			hidden_layers = hidden_str.split(",")
		 			layers.extend(hidden_layers)
		 			biases = bias_str.split(",")
		 			layers.append(output_count)
		 			layers = map(int,layers)
		 			biases = map(int,biases)
					
					if(len(layers) > 0 and len(biases) > 0):
		 				self.render_neural_net_visualization(layers,biases)

 		def render_input_field(default_value, label_text,desc_text,width,parent_frame,command=None):
 			widget_frame = Frame(parent_frame)
 			widget_frame.pack(fill=X,expand=False)
 			desc_frame = Frame(widget_frame, width=50)
 			desc_frame.pack(side=BOTTOM,expand=False)
 			text_input = Entry(widget_frame, width=width)
 			text_input.bind("<KeyRelease>", render_nn_vis_trigger)
 			text_input.insert(0,str(default_value))
 			text_input.pack(side=RIGHT)
 			input_label = Label(widget_frame, text=label_text+": ",font=(self.font_face, self.main_font_size))
 			input_label.pack(side=LEFT)
 			label_desc = Label(desc_frame, text="*"+desc_text, font=(self.font_face, 10), fg="#60606b",wraplength=210)
 			label_desc.pack(side=BOTTOM)
 			return text_input

 		#show_visual_nn_opt = render_option("NETWORK VISUALIZATION", self.render_neural_net_visualization, self.ui_frame)
 		render_nn_vis_trigger()

 		self.data_set_name_input_label = render_input_field("newdataset.txt", "Dataset file","Save a text file into the current directory and enter name here",input_text_length,self.learn_options_frame)
 		self.data_to_retrieve_input_label = render_input_field("25000", "Data To Use","Enter 'all' or number",input_text_length,self.learn_options_frame)
 		self.matrix_dim_input_label = render_input_field(default_input_dims,"Matrix Input Dimensions","Enter height, width of matrix",input_text_length,self.learn_options_frame,command=render_nn_vis_trigger)
 		self.output_count_input_label = render_input_field(default_output_count, "Output Count","Enter output quantity",input_text_length,self.learn_options_frame,command=render_nn_vis_trigger)
 		self.hidden_layer_input_label = render_input_field(default_hidden_layers_str, "Hidden Layers", "Enter comma seperated list of layer sizes",input_text_length, self.learn_options_frame,command=render_nn_vis_trigger)
 		self.bias_vals_input_label = render_input_field(default_bias_str, "Bias Values", "List must match hidden layer count plus output, but enter 0 for no bias",input_text_length,self.learn_options_frame,command=render_nn_vis_trigger)
 		self.learning_rate_input_label = render_input_field("0.5", "Learning Rate","Enter decimal or integer",input_text_length,self.learn_options_frame)
 		self.weight_range_input_label = render_input_field("-1,1", "Weight Ranges","Enter one value (or two for a range) for initial weight values",input_text_length, self.learn_options_frame)
 		self.epochs_input_label = render_input_field("10", "Epochs","Total number of iterations",input_text_length, self.learn_options_frame)
 		self.test_data_partition_input_label = render_input_field("2000", "Data for Testing","Amount of data to partition from dataset for result testing",input_text_length, self.learn_options_frame)
 		self.start_learning_opt = render_option("START LEARNING", self.start_learning_ui_request, self.learn_options_frame)
 		self.cancel_learning_opt = render_option("STOP", self.cancel_learning, self.learn_options_frame)
 		self.cancel_learning_opt.config(state="disabled")
 		self.clear_graphs_opt = render_option("CLEAR GRAPHS", self.clear_graphs, self.learn_options_frame)
 		self.render_cam_opt = render_option("TEST WITH CAM", self.render_camera, self.learn_options_frame)
 		self.render_cam_opt.config(state="disabled")
 		self.test_input_fname_label = render_input_field("", "Test Image File","Enter the name of file to test",input_text_length, self.learn_options_frame)
 		self.test_input_opt = render_option("TEST", self.test_input_from_file, self.learn_options_frame)
 		self.test_input_opt.config(state="disabled")


 	def check_str_list_valid(self,string):
 		valid_str_entry = True
 		for char in string:
 			if(char!="," and char.isdigit()==False):
 				valid_str_entry = False
 				break

 		return valid_str_entry

 	prev_guess = -1
 	def render_camera(self):
 		camera_window = Toplevel(self.tk_main)
 		image_frame = Frame(camera_window, width=600, height=500)
		image_frame.pack()
		capture_frame = cv2.VideoCapture(0)
		label_for_cam = Label(image_frame)
		label_for_cam.pack()

		mini_cam_window = Toplevel(self.tk_main,width=300,height=300)
		imagemini_frame = Frame(mini_cam_window, width=600, height=500)
		imagemini_frame.pack()
		label_for_minicam = Label(imagemini_frame)
		label_for_minicam.pack()
		self.attempt_group = []

		def render_cam_frame():
			_, cv_frame = capture_frame.read()
			cv_frame = cv2.cvtColor(cv_frame, cv2.COLOR_BGR2GRAY)
			roi_size = 50
			roi_point_1 = (400,200)
			roi_point_2 = (roi_point_1[0]+roi_size,roi_point_1[1]+roi_size)
			roi_matrix = cv_frame[roi_point_1[1]:roi_point_2[1],roi_point_1[0]:roi_point_2[0]]
			_,roi_matrix = cv2.threshold(roi_matrix,120,255,cv2.THRESH_BINARY_INV)
			
			img_miniframe = Image.fromarray(roi_matrix)
			tk_miniframe = ImageTk.PhotoImage(image=img_miniframe)
			label_for_minicam.imgtk = tk_miniframe
			label_for_minicam.configure(image=tk_miniframe)
			roi_matrix = cv2.resize(roi_matrix, (self.matrix_dims[0],self.matrix_dims[1]))
			matrix_float = self.matrix_data_loader.prep_matrix_for_input(roi_matrix)
			outline_vals = [matrix_float[0,:-1], matrix_float[:-1,-1], matrix_float[-1,::-1], matrix_float[-2:0:-1,0]]
			outline_sum = np.concatenate(outline_vals).sum()

			if(outline_sum>0):
				if(len(self.attempt_group)>0):
					print(max(self.attempt_group,key=self.attempt_group.count))
				self.attempt_group = []
			else:
			  	self.neural_network.feed_forward(matrix_float)
			  	output_neurons = self.neural_network.nn_neurons[-1].tolist()
			  	max_val = max(output_neurons)
			  	if(max_val > 0.9):
			  		guess_val = output_neurons.index(max_val)
			  		print(guess_val)
			  		self.attempt_group.append(guess_val)

			cv2.rectangle(cv_frame,roi_point_1,roi_point_2, (255), thickness=3, lineType=8, shift=0)

			img_frame = Image.fromarray(cv_frame)
			tk_frame = ImageTk.PhotoImage(image=img_frame)
			label_for_cam.imgtk = tk_frame
			label_for_cam.configure(image=tk_frame)
			label_for_cam.after(10, render_cam_frame) 

		render_cam_frame()

	def test_input_from_file(self):
		file_name = self.test_input_fname_label.get() 
		file_type_pos = file_name.rfind(".")
		file_type_str = file_name[file_type_pos+1:]
		image_files = ["png","jpg"]
		print(file_name)
		print(file_type_str)
		if(file_type_str in image_files):
			image_matrix = cv2.imread(file_name)
			image_matrix = cv2.cvtColor(image_matrix, cv2.COLOR_BGR2GRAY)
			image_matrix = cv2.resize(image_matrix, (self.matrix_dims[0],self.matrix_dims[1]))
			matrix_float = self.matrix_data_loader.prep_matrix_for_input(image_matrix)
			print(matrix_float)
			self.neural_network.feed_forward(matrix_float)
			output_neurons = self.neural_network.nn_neurons[-1].tolist()
			output_pos_result = output_neurons.index(max(output_neurons))
			self.print_console("**OUTPUT RESULT: " + str(output_pos_result))
   

 	def cancel_learning(self):
 		self.cancel_training = True
 		self.prepare_new_line_graph()
 		self.start_learning_opt.config(state="normal")
 		self.cancel_learning_opt.config(state="disabled")
 		if(self.input_neuron_count>0):
 			self.render_cam_opt.config(state="normal")
 			self.test_input_opt.config(state="normal")

 	def print_console(self,text):
 		self.console_list_box.configure(state="normal")
 		if(text==" **TRAINING** \n"):
 			text += ">>With graph line color: "+self.line_colors[self.new_line_count-1]
 		self.console_list_box.insert(END,">>" + text + "\n")
 		self.console_list_box.see(END)
 		self.console_list_box.configure(state="disabled")
 

 	def check_all_fields_valid(self):
 		hidden_str = self.hidden_layer_input_label.get()
 		bias_str = self.bias_vals_input_label.get()
 		error = ""
 		valid_values = {}
 		if(self.check_str_list_valid(hidden_str+bias_str) == False or hidden_str == "" or bias_str == ""):
 			error = "You hidden layers or bias values are invalid"
 		else:
	 		valid_values['hidden_layers'] = map(int,hidden_str.split(","))
	 		valid_values['biases_for_non_input_layers'] = map(int,bias_str.split(","))

	 		if(len(valid_values['hidden_layers'])+1 != len(valid_values['biases_for_non_input_layers'])):
	 			error = "Bias count must be equal to "+str(len(valid_values['hidden_layers'])+1)+" (the total layer count expect input)"
 		
 		learning_constant = self.learning_rate_input_label.get()
 		if(learning_constant.replace(".", "", 1).isdigit() == False):
 			error = "Invalid learning constant"
 		else:
 			valid_values['learning_constant'] = float(learning_constant)
 		valid_values['data_file_name'] = self.data_set_name_input_label.get()
 		matrix_dims_str = self.matrix_dim_input_label.get()
 		weight_range_str = self.weight_range_input_label.get()
 		to_retreive = self.data_to_retrieve_input_label.get()
 		output_count = self.output_count_input_label.get()
 		epochs = self.epochs_input_label.get()
 		data_to_test_count = self.test_data_partition_input_label.get()
 		if(self.check_str_list_valid(matrix_dims_str)==False):
 			error = "Invalid matrix dimensions"
 		else:
 			valid_values['matrix_dims'] = map(int,matrix_dims_str.split(","))
 		if(self.check_str_list_valid(weight_range_str.replace(".", "", 1).replace("-", "", 1))==False):
 			error = "Invalid weight ranges"
 		else:
 			valid_values['weight_range'] = map(float,weight_range_str.split(","))
 		if(to_retreive.isdigit() == False):
 			error = "Invalid matrices to use entry"
 		else:
 			valid_values['to_retreive'] = int(to_retreive)
 		if(output_count.isdigit() == False):
 			error = "Invalid output count"
 		else:
 			valid_values['output_count'] = int(output_count)
 		if(epochs.isdigit() == False):
 			error = "Invalid epochs entry"
 		else:
 			valid_values['epochs'] = int(epochs)
 		if(data_to_test_count.isdigit() == False):
 			error = "Invalid epochs entry"
 		else:
 			valid_values['data_to_test'] = int(data_to_test_count)
 			if(valid_values['data_to_test'] > valid_values['to_retreive']):
 				error = "Data to test amount cannot be more than all data to get"

 		valid_values['success'] = True

 		if(error == ""):
 			return valid_values
 		else:
 			response = {}
 			response['success'] = False
 			response['error'] = error
 			return response

 	def start_learning_ui_request(self):
 		self.cancel_training = False
 		self.can_clear_graph = True
 		self.field_result = self.check_all_fields_valid()
 		if(self.field_result['success'] ==True):
 			self.start_learning_opt.config(state="disabled")
 			self.cancel_learning_opt.config(state="normal")
 			thread.start_new_thread(self.start_learning_in_thread,())
 		else:
	 		tkMessageBox.showinfo("Error", self.field_result['error'])


	matrix_data = []
	matrix_targets = []
	curr_dataset_name = ""
	input_neuron_count = 0
 	def start_learning_in_thread(self):
 		field_result = self.field_result
	 	testing_mode = False

		if(len(self.matrix_data)!=field_result['to_retreive'] or field_result['data_file_name'] != self.curr_dataset_name):
			self.curr_dataset_name = field_result['data_file_name']
			self.matrix_dims = field_result['matrix_dims']
			self.matrix_data_loader = matrix_data_loader_handler(field_result['matrix_dims'],field_result['to_retreive'],field_result['data_file_name'],self)
			self.matrix_data_loader.populate_matrices()
			self.input_neuron_count = self.matrix_data_loader.matrix_width * self.matrix_data_loader.matrix_height
			self.matrix_data = self.matrix_data_loader.matrices
			self.matrix_targets = self.matrix_data_loader.targets
 		
 		self.neural_network = neural_network_handler()
 		self.neural_network.initilize_nn(field_result['hidden_layers'],
	 			self.input_neuron_count,field_result['output_count'], self.matrix_data,self.matrix_targets,
	  			field_result['biases_for_non_input_layers'], field_result['learning_constant'], 
	  			testing_mode,field_result['weight_range'],field_result['epochs'],field_result['data_to_test'],
	  			self)
 		self.neural_network.train()

	def render_neural_net_visualization(self,layers,biases):
		self.tk_nn_visual_canvas.delete("all")
		for old_labels in self.canvas_labels:
			old_labels.destroy()

		example_p_limit_count = 20 #zero for all
		highest_layer_count = max(layers)
		if(highest_layer_count > example_p_limit_count):
			highest_layer_count = example_p_limit_count

		highest_layer_height = 0

		if(len(layers)-1 != len(biases)):
			diff_b_layers = len(layers)-1 - len(biases)
			if(diff_b_layers < 0):
				biases = biases[0:diff_b_layers]
			else:
				for i in range(diff_b_layers):
					biases.append(0)

		neuron_padding = 5		
		neuron_radius = int((((self.canvas_height / highest_layer_count)/2)-neuron_padding))
		if(neuron_radius > 15): neuron_radius = 15
		neuron_x = neuron_radius + 20
		neuron_dist_x = (self.canvas_width / (len(layers)-1)) - neuron_x*2
		neuron_color = "blue"

		bias_pos_diff_x = 50
		bias_pos_diff_y = 50
		bias_color = "green"
		bias_pos_y = neuron_radius*2

		def get_layer_height_px(layer_count):
			return (layer_count*(neuron_radius*2 + neuron_padding))

		for neuron_layer in range(0,len(layers)):
			length_of_layer = layers[neuron_layer]
			if(example_p_limit_count > 0 and example_p_limit_count < length_of_layer):
				length_of_layer = example_p_limit_count
			curr_layer_height = get_layer_height_px(length_of_layer)
			if(curr_layer_height > highest_layer_height):
				highest_layer_height = curr_layer_height

		for neuron_layer in range(0,len(layers)):
			length_of_layer = layers[neuron_layer]
			if(example_p_limit_count > 0 and example_p_limit_count < length_of_layer):
				length_of_layer = example_p_limit_count

			neuron_ystart = (self.canvas_height - get_layer_height_px(length_of_layer))/2
			neuron_y = neuron_ystart
			layer_has_bias = ((neuron_layer > 0) and (biases[neuron_layer-1] != 0))
			
			if layer_has_bias == True:
				bias_y_pos = 10
				bias_x_pos = neuron_x-bias_pos_diff_x
				bias_oval = self.tk_nn_visual_canvas.create_oval(bias_x_pos-neuron_radius,bias_y_pos-neuron_radius,bias_x_pos+neuron_radius,bias_y_pos+neuron_radius, fill=bias_color,outline=bias_color)
				self.tk_nn_visual_canvas.tag_raise(bias_oval)

			for single_neuron in range(0,length_of_layer):
				if(single_neuron == 0):
					real_layer_count = layers[neuron_layer]
					extra_str_label = ""
					if(real_layer_count > length_of_layer):
						extra_str_label = "^\n^\n"
					self.canvas_labels.append(Label(self.tk_nn_visual_canvas, text=extra_str_label+str(real_layer_count)))
					self.canvas_labels[-1].place(x=neuron_x-(neuron_radius*2), y=neuron_y-(neuron_radius*3))

				neuron_oval = self.tk_nn_visual_canvas.create_oval(neuron_x-neuron_radius,neuron_y-neuron_radius,neuron_x+neuron_radius,neuron_y+neuron_radius,fill=neuron_color,outline=neuron_color)
				self.tk_nn_visual_canvas.tag_raise(neuron_oval)

				if(layer_has_bias == True):
					bias_connector = self.tk_nn_visual_canvas.create_line(neuron_x, neuron_y, bias_x_pos,bias_y_pos)
					self.tk_nn_visual_canvas.tag_lower(bias_connector)

				neuron_dist_y = (neuron_radius*2) + neuron_padding
				if(neuron_layer < len(layers)-1):
					length_of_next_layer = layers[neuron_layer+1]
					if(example_p_limit_count > 0 and example_p_limit_count < length_of_next_layer):
						length_of_next_layer = example_p_limit_count
					neuron_y_for_line = (self.canvas_height - (length_of_next_layer)*(neuron_radius*2 + neuron_padding))/2
					
					for neuron_weights in range(0,length_of_next_layer):
						neuron_connector = self.tk_nn_visual_canvas.create_line(neuron_x, neuron_y, neuron_x+neuron_dist_x, neuron_y_for_line)
						self.tk_nn_visual_canvas.tag_lower(neuron_connector)

						neuron_y_for_line += neuron_dist_y

				neuron_y += neuron_dist_y
			neuron_x += neuron_dist_x
		
class neural_network_handler:

	#construct object to develop specific network structure
	def initilize_nn(self, hidden_layers,
	 				input_count, output_count, matrix_data,matrix_targets,
	  				biases_for_non_input_layers, learning_constant,
	  				testing_mode,weight_range,epochs,data_to_test,user_interface):

		self.user_interface = user_interface
		if(self.user_interface.cancel_training == False):
		
			self.user_interface.print_console("\n\n\n--------------------------- \n Constructing neural network \n\n")
			self.all_weights = []
			self.nn_neurons = []
			self.weight_changes = []
			self.biases_weights = []
			self.biases_weight_changes = []
			self.epochs = epochs
			self.test_data_amount = data_to_test
			self.matrix_data = matrix_data
			self.hidden_layers = hidden_layers
			self.matrix_targets = matrix_targets
			self.learning_constant = learning_constant
			self.output_count = output_count
			self.input_count = input_count
			self.testing_mode = testing_mode
			self.biases_for_non_input_layers = biases_for_non_input_layers
			self.weight_range = weight_range 
			self.success_records = []
			self.populate_nn_neurons()
			self.populate_all_weights()

	def populate_nn_neurons(self):
		nn_inputs = np.zeros(self.input_count)
		nn_outputs = np.zeros(self.output_count)
		self.nn_neurons.append(nn_inputs)
		for i in self.hidden_layers:
			hidden_layer = np.zeros(i)
			self.nn_neurons.append(hidden_layer)
		self.nn_neurons.append(nn_outputs)

	def populate_all_weights(self):
		for neuron_layer in range(1, len(self.nn_neurons)):
			layer_length = len(self.nn_neurons[neuron_layer])
			weight_layer = []
			weight_changes_layer = []
			for single_neuron in range(0, layer_length):
				prev_layer_count = len(self.nn_neurons[neuron_layer-1])
				neuron_weights = self.initilize_weights(prev_layer_count)
				weights_change_record_neuron = np.zeros(prev_layer_count)
		
				weight_layer.append(neuron_weights)
				weight_changes_layer.append(weights_change_record_neuron)

			self.all_weights.append(weight_layer)
			self.weight_changes.append(weight_changes_layer)

		for layer_count in range(0, len(self.biases_for_non_input_layers)):
			single_bias_weights = []
			single_bias_weights_change = []
			if(self.biases_for_non_input_layers[layer_count]!=0):
				bias_input_count = len(self.nn_neurons[layer_count+1])
				single_bias_weights = self.initilize_weights(bias_input_count)
				single_bias_weights_change = np.zeros(bias_input_count)
			self.biases_weights.append(single_bias_weights)
			self.biases_weight_changes.append(single_bias_weights_change)

	def initilize_weights(self,size):
		if(len(self.weight_range)==1):
			upper_bound = self.weight_range[0]
			lower_bound = upper_bound
		else:
			upper_bound = self.weight_range[1]
			lower_bound = self.weight_range[0]

		return np.random.uniform(low=lower_bound, high=upper_bound, size=(size))

	def feed_forward(self, matrix):
		self.populate_input_layer(matrix)
		for after_input_layer in range(1, len(self.nn_neurons)):
			for neuron_count in range(0, len(self.nn_neurons[after_input_layer])):
				relevant_weights = self.all_weights[after_input_layer-1][neuron_count]
				hidden_neuron_sum = np.dot(relevant_weights, self.nn_neurons[after_input_layer-1])
				if(len(self.biases_weights[after_input_layer-1])!=0):
					hidden_neuron_sum += self.biases_for_non_input_layers[after_input_layer-1] * self.biases_weights[after_input_layer-1][neuron_count]
				self.nn_neurons[after_input_layer][neuron_count] = self.activate_threshold(hidden_neuron_sum, "sigmoid")




	def populate_input_layer(self, data):
		value_count = 0
		if(type(data[0]) is not int):
			self.nn_neurons[0] = data.flatten()
		else:
			self.nn_neurons[0] = np.array(data)

	testing_output_mode = False
	test_counter = 0
	correct_count = 0
	error_by_1000 = 0
	error_by_1000_counter = 1
	output_error_total = 0
	
	def back_propagate(self, target_val,repeat_count):
		
		if(len(self.nn_neurons[-1])>1 and type(target_val) is int):
			target_vector = self.populate_target_vector(target_val)
		else:
			target_vector = target_val
		self.output_error_total = 0.5*((self.nn_neurons[-1] - target_vector)**2).sum()
		
		outputs_as_list = self.nn_neurons[-1].tolist()
		if(self.test_counter >= len(self.matrix_data)-self.test_data_amount):
			if(outputs_as_list.index(max(outputs_as_list))==target_val):
				self.correct_count += 1

		if(outputs_as_list.index(max(outputs_as_list))!=target_val):
				self.error_by_1000  +=1
		if(self.error_by_1000_counter % 1000 == 0):
			self.user_interface.animate_graph_figures(0,self.error_by_1000/10)
			self.error_by_1000 = 0
			self.error_by_1000_counter = 0

		for weight_layer_count in range(len(self.all_weights)-1,-1,-1):
			weight_neuron_vals = np.expand_dims(self.nn_neurons[weight_layer_count+1],axis=1)
			target_vector = np.expand_dims(target_vector,axis=1)
			activated_to_sum_step = weight_neuron_vals * (1-weight_neuron_vals)
			if(weight_layer_count == len(self.all_weights)-1):
				back_prop_cost_to_sum = (weight_neuron_vals - target_vector) * activated_to_sum_step
			else:
				back_prop_cost_to_sum = np.dot(np.asarray(self.all_weights[weight_layer_count+1]).transpose(),back_prop_cost_to_sum) * activated_to_sum_step

			if(len(self.biases_weights[weight_layer_count])!=0):
				self.biases_weights[weight_layer_count] = back_prop_cost_to_sum
			input_neuron_vals = np.expand_dims(self.nn_neurons[weight_layer_count],axis=1)
			full_back_prop_sum_to_input = np.dot(back_prop_cost_to_sum,input_neuron_vals.transpose())
			current_weight_vals = self.all_weights[weight_layer_count]
			new_weight_vals = current_weight_vals - (self.learning_constant * full_back_prop_sum_to_input)
			self.all_weights[weight_layer_count] = new_weight_vals
	
		self.test_counter += 1
		self.error_by_1000_counter += 1

	def train(self):
		if(self.user_interface.cancel_training == False):
			success_list = []
			hidden_layer_str = ""
			for layerc in self.hidden_layers:
				hidden_layer_str += str(layerc)+","
			hidden_layer_str = hidden_layer_str[0:-1]
			cancel_training = False
			self.user_interface.print_console(" **TRAINING** \n")
			self.user_interface.print_console("With learning rate: " + str(self.learning_constant))
			self.user_interface.print_console("With hidden layers: " + str(hidden_layer_str))
			self.user_interface.print_console("With test amount by epoch size: " + str(self.test_data_amount)+"/"+str(len(self.matrix_targets)))
			self.user_interface.print_console("With epoch count: " + str(self.epochs))

			if(self.testing_mode == True):
				self.repeat_count = 5000
			for epoch in range(0,self.epochs):
				matrix_count = 0
				for matrix in self.matrix_data:
					if(self.user_interface.cancel_training == True):
						break
					target_val = self.matrix_targets[matrix_count]
					self.feed_forward(matrix)
					self.back_propagate(target_val,epoch)
					matrix_count += 1
				if(self.user_interface.cancel_training == True):
					break

				success_p = (float(self.correct_count)/float(self.test_data_amount))*100
				self.user_interface.animate_graph_figures(1,success_p)
				success_list.append(success_p)
				self.test_counter = 0
				self.correct_count = 0

			if(len(success_list)>0):
				av_success = sum(success_list)/len(success_list)
				highest_success = max(success_list)
			else:
				av_success = "N/A"
				highest_success = "N/A"
			training_done_msg = "**FINISHED**"
			if(self.user_interface.cancel_training == True):
				training_done_msg = "**CANCELLED**"
			else:
				self.user_interface.cancel_learning()
			self.user_interface.print_console(training_done_msg)
			self.user_interface.print_console("AVERAGE SUCCESS: " + str(av_success) + "%")
			self.user_interface.print_console("HIGHEST SUCCESS: " + str(highest_success) + "%")

	def activate_threshold(self,value, type):
		if(type == "step"):
			if(value>=0.5):
				return 1
			else:
				return 0
		elif(type == "sigmoid"):
			return 1/(1+(math.exp(-value)))

	def populate_target_vector(self,target):
		vector = []
		for i in range(0,self.output_count):
			vector.append(0)
		vector[target] = 1
		return vector

def main():
	tk_main = Tk()
	user_interface = user_interface_handler(tk_main)
	tk_main.mainloop()
	
main()
