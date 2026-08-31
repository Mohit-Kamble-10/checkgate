import re
from configs.anpr_config import * 

class post_processing():
    def __init__(self) -> None:
        pass
    def process_state_code(self,in_state_code):
        # print('in_state_code : ',in_state_code)
        if in_state_code in state_code_dict.keys():
            return in_state_code,0
        else:
            for state_code_txt,data_lst in state_code_dict.items():
                if in_state_code in data_lst:
                    return state_code_txt,0
            return in_state_code,1#'Manual Check Required'

    def process_dist_code(self,in_dist_code,flag='dist_code'):#flag for dist_code or last_int_seires 4
        final_dist_code=''
        for number in in_dist_code:
            if number in dist_code_dict.keys():
                final_dist_code+=number
            else:
                for dist_code_txt,data_lst in dist_code_dict.items():
                    if number in data_lst:
                        final_dist_code+=dist_code_txt
                        
        # print('final_dist_code : ',final_dist_code)
        if flag=='dist_code' and len(final_dist_code)==2 and final_dist_code.isnumeric():
            return final_dist_code,0
        elif flag=='last_int_seires' and len(final_dist_code)>2 and final_dist_code.isnumeric():
            return final_dist_code,0
        else:
            return final_dist_code,1#'Manual Check Required'
        
        
    def process_series(self,in_series):# one or two chars
        # print('process_series : ',in_series)
        # print('last_number : ',self.last_number)
        # print(' len(self.Predicted_number_plate) : ', len(self.Predicted_number_plate))
        
        final_series_code=''
        for index,char_txt in enumerate(in_series):
            # print(index,char_txt.isnumeric() ,  self.last_number.isnumeric())
            if char_txt.isnumeric() and index==1 and self.last_number.isnumeric()==False:
                final_series_code+=char_txt
                # print('final_series_code 1:',final_series_code)
            elif char_txt in in_series_dict.keys():
                final_series_code+=char_txt
                # print('final_series_code 2:',final_series_code)
            elif char_txt.isnumeric() and index==1 and self.last_number.isnumeric() and len(self.Predicted_number_plate)==9: 
                final_series_code+=char_txt
                # print('final_series_code 3:',final_series_code)
            else:
                for series_code_txt,data_lst in in_series_dict.items():
                    if char_txt in data_lst:
                        final_series_code+=series_code_txt

                        # print('final_series_code 4:',final_series_code)
            
        if len(final_series_code)==2:

            # print('final_series_code 5:',final_series_code)
            return final_series_code,0
        else:

            # print('final_series_code 5:',final_series_code)
            return final_series_code,1#'Manual Check Required'
    def Replace_IO_dist_code(self):
        self.dist_code=self.dist_code.replace('I','1')
        self.dist_code=self.dist_code.replace('O','0')
        
    def process_text(self):
        processed_str=''
            
        self.Replace_IO_dist_code()
        process_state_code_output,process_state_code_Flag=self.process_state_code(self.state_code)
        # print('process_state_code_output : ',process_state_code_output)
        processed_str+=process_state_code_output

        process_dist_code_output,process_dist_code_Flag=self.process_dist_code(self.dist_code,flag='dist_code')
        processed_str+=process_dist_code_output
        
        process_series_output,process_series_Flag=self.process_series(self.series)
        processed_str+=process_series_output
        
        process_dist_code_output_last_series,process_dist_code_last_series_Flag=self.process_dist_code(self.last_number,flag='last_int_seires')
        processed_str+=process_dist_code_output_last_series

        return processed_str,process_state_code_Flag,process_dist_code_Flag,process_series_Flag,process_dist_code_last_series_Flag

    def main(self,Predicted_number_plate):
        processed_str=''
        self.Predicted_number_plate=Predicted_number_plate
        if len(Predicted_number_plate)>8 and len(Predicted_number_plate)<11:#9 and 10
            self.state_code=Predicted_number_plate[:2]
            self.dist_code=Predicted_number_plate[2:4]
            self.series=Predicted_number_plate[4:6]
            self.last_number=Predicted_number_plate[6:]
            if self.state_code=='BH':
                return Predicted_number_plate
            
            processed_str,process_state_code_Flag,process_dist_code_Flag,process_series_Flag,process_dist_code_last_series_Flag = self.process_text()
            

            if (process_state_code_Flag or process_dist_code_Flag or process_series_Flag or process_dist_code_last_series_Flag)==1:
                 return processed_str,'2'#'Further analysis required'
            else:
                return processed_str,'Success'
            
            # processed_str+=self.process_state_code(self.state_code)
            # processed_str+=self.process_dist_code(self.dist_code)
            # processed_str+=self.process_series(self.series)
            # processed_str+=self.process_dist_code(self.last_number)
            # if 'Manual Check Required' in processed_str:
            #     return processed_str,'Further analysis required'
            # else:
            #     return processed_str,'Success'

        elif len(Predicted_number_plate)>10:
            # print('else len : ',len(Predicted_number_plate)-10)
            found_list=[]
            for i in range(len(Predicted_number_plate)-9):
                # print('='*40)
                # print('i : ',i)

                # check_state_str=Predicted_number_plate[i:i+2] 
                
                Predicted_number_plate_crop=Predicted_number_plate[i:10+i]
                # print('Predicted_number_plate_crop : ',i,' : ',Predicted_number_plate_crop)
                if len(Predicted_number_plate_crop)>8 and len(Predicted_number_plate_crop)<11:#9 and 10
                    
                    self.state_code=Predicted_number_plate_crop[:2]
                    self.dist_code=Predicted_number_plate_crop[2:4]
                    self.series=Predicted_number_plate_crop[4:6]
                    self.last_number=Predicted_number_plate_crop[6:]

                    processed_str,process_state_code_Flag,process_dist_code_Flag,process_series_Flag,process_dist_code_last_series_Flag = self.process_text()

                    # print('processed_str : ',processed_str,process_state_code_Flag , process_dist_code_Flag , process_series_Flag , process_dist_code_last_series_Flag)
                    if (process_state_code_Flag or process_dist_code_Flag or process_series_Flag or process_dist_code_last_series_Flag)==1:
                        # print(processed_str,'2')
                        # return processed_str,'2'#'Further analysis required'
                        pass
                    else:
                        # print(processed_str,'Success')
                        found_list.append(processed_str)
                        # return processed_str,'Success'
                

            if len(found_list)>0:
                return found_list[0],'Success'
            else:
                return Predicted_number_plate,'>8 and < 11 Error'

            
        else:
            return Predicted_number_plate,'>8 and < 11 Error'
            


class post_processing_old():
    # till 06-04-2024
    def __init__(self) -> None:
        pass
    def process_state_code(self,in_state_code):
        # print('in_state_code : ',in_state_code)
        if in_state_code in state_code_dict.keys():
            return in_state_code,0
        else:
            for state_code_txt,data_lst in state_code_dict.items():
                if in_state_code in data_lst:
                    return state_code_txt,0
            return in_state_code,1#'Manual Check Required'

    def process_dist_code(self,in_dist_code):
        final_dist_code=''
        for number in in_dist_code:
            if number in dist_code_dict.keys():
                final_dist_code+=number
            else:
                for dist_code_txt,data_lst in dist_code_dict.items():
                    if number in data_lst:
                        final_dist_code+=dist_code_txt
        # print('final_dist_code : ',final_dist_code)
        if len(final_dist_code)>=2 and final_dist_code.isnumeric():
            return final_dist_code,0
        else:
            return final_dist_code,1#'Manual Check Required'
        
    def process_series(self,in_series):# one or two chars
        final_series_code=''
        for index,char_txt in enumerate(in_series):
            if char_txt.isnumeric() and index==1:
                final_series_code+=char_txt
            elif char_txt in in_series_dict.keys():
                final_series_code+=char_txt
            else:
                for series_code_txt,data_lst in in_series_dict.items():
                    if char_txt in data_lst:
                        final_series_code+=series_code_txt
        if len(final_series_code)==2:
            return final_series_code,0
        else:
            return final_series_code,1#'Manual Check Required'
    def Replace_IO_dist_code(self):
        self.dist_code=self.dist_code.replace('I','1')
        self.dist_code=self.dist_code.replace('O','0')
        

    def main(self,Predicted_number_plate):
        processed_str=''
        if len(Predicted_number_plate)>8 and len(Predicted_number_plate)<11:#9 and 10
            self.state_code=Predicted_number_plate[:2]
            self.dist_code=Predicted_number_plate[2:4]
            self.series=Predicted_number_plate[4:6]
            self.last_number=Predicted_number_plate[6:]

            if self.state_code.isnumeric() and self.dist_code=='BH':
                return Predicted_number_plate
            
            self.Replace_IO_dist_code()
            process_state_code_output,process_state_code_Flag=self.process_state_code(self.state_code)
            # print('process_state_code_output : ',process_state_code_output)
            processed_str+=process_state_code_output

            process_dist_code_output,process_dist_code_Flag=self.process_dist_code(self.dist_code)
            processed_str+=process_dist_code_output
            
            process_series_output,process_series_Flag=self.process_series(self.series)
            processed_str+=process_series_output
            
            process_dist_code_output_last_series,process_dist_code_last_series_Flag=self.process_dist_code(self.last_number)
            processed_str+=process_dist_code_output_last_series

            if (process_state_code_Flag or process_dist_code_Flag or process_series_Flag or process_dist_code_last_series_Flag)==1:
                 return processed_str,'2'#'Further analysis required'
            else:
                return processed_str,'Success'
            
            # processed_str+=self.process_state_code(self.state_code)
            # processed_str+=self.process_dist_code(self.dist_code)
            # processed_str+=self.process_series(self.series)
            # processed_str+=self.process_dist_code(self.last_number)
            # if 'Manual Check Required' in processed_str:
            #     return processed_str,'Further analysis required'
            # else:
            #     return processed_str,'Success'

        elif len(Predicted_number_plate)>10:
            for i in range(len(Predicted_number_plate)-1):
                check_state_str=Predicted_number_plate[i:i+2] 
                if 'Manual Check Required' in self.process_state_code(check_state_str):
                    pass
                else:
                    Predicted_number_plate=Predicted_number_plate[i:]
                    if len(Predicted_number_plate)>8 and len(Predicted_number_plate)<11:#9 and 10
                        self.state_code=Predicted_number_plate[:2]
                        self.dist_code=Predicted_number_plate[2:4]
                        self.series=Predicted_number_plate[4:6]
                        self.last_number=Predicted_number_plate[6:]
                        processed_str+=self.process_state_code(self.state_code)[0]
                        processed_str+=self.process_dist_code(self.dist_code)[0]
                        processed_str+=self.process_series(self.series)[0]
                        processed_str+=self.process_dist_code(self.last_number)[0]
                        if 'Manual Check Required' in processed_str:
                            return processed_str,'2'#'Further analysis required'
                        else:
                            return processed_str,'Success'
                    else:
                        return Predicted_number_plate,'Length < 9 clip Error'



            
        else:
            return Predicted_number_plate,'>8 and < 11 Error'
            