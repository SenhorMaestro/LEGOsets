import logging
import time
import pandas as pd
from PIL import Image
from ultralytics import YOLO
from torchvision import transforms as T
from scipy.spatial.distance import hamming


from aiogram import Bot, Dispatcher, executor, types, filters
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery

from config import TOKEN, ADMIN_ID

logging.basicConfig(filename = 'logfile.log', level=logging.INFO)

bot = Bot(token=TOKEN)
dp = Dispatcher(bot)
admin_id = ADMIN_ID

model = YOLO("weights_v3_medium_200/weights/best.pt")
df = pd.read_csv('LEGOdata.csv')

@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    user_name = message.from_user.full_name
    user_id = message.from_user.id
    t = time.localtime()
    text = f'Привет , {user_name}. Я телеграм-бот , знающий всё о LEGO наборах. Сфотографируй мне лицевую сторону коробки или просто введи номер , и я найду тебе инструкцию или всю нужную информацию о том , где купить набор или насколько он вырастет в цене в будущем.\n Дополнительная помощь тут : /help'
    logging.info(f"{user_name=} {user_id=} sent message: {message.text} at {time.asctime(t)}")
    await message.reply(text)

@dp.message_handler(commands=['fav'])
async def send_welcome(message: types.Message):
    user_name = message.from_user.full_name
    user_id = message.from_user.id
    t = time.localtime()
    logging.info(f"{user_name=} {user_id=} sent message: {message.text} at {time.asctime(t)}")
    df = pd.read_csv('LEGOdata.csv')
    list_fav = df[df['tg id']==user_id]['номер набора'].unique().tolist()
    text = 'Ваше избранное :\n'
    for i in list_fav:
        text += '/set_'+str(i)+'\n'
    await message.reply(text)

@dp.message_handler(commands=['zam'])
async def send_welcome(message: types.Message):
    user_name = message.from_user.full_name
    user_id = message.from_user.id
    t = time.localtime()
    logging.info(f"{user_name=} {user_id=} sent message: {message.text} at {time.asctime(t)}")
    df = pd.read_csv('LEGOdata.csv')
    text = 'Ваши заметки :\n'
    await message.reply(text)
    text3 = ''
    for i in range(len(df)):
        text1 = ''
        text2 = ''
        if (df['tg id'][i]==user_id) & (pd.notna(df['заметки'][i])):
            text1 = '/set_' + str(df['номер набора'][i]) +'\n'
            text2 = str(df['заметки'][i])+2*'\n'
        text3 += text1+text2
    await message.reply(text3)
    

@dp.message_handler(commands=['vkus'])
async def send_welcome(message: types.Message):
    user_name = message.from_user.full_name
    user_id = message.from_user.id
    t = time.localtime()
    logging.info(f"{user_name=} {user_id=} sent message: {message.text} at {time.asctime(t)}")
    df = pd.read_csv('LEGOdata.csv')
    indexes = list(set(df['номер набора']))
    columns = list(set(df['tg id']))
    df_corr = pd.DataFrame(columns=columns, index=indexes)
    for set_no in indexes:
        for chel in columns:
            if set_no in df[df['tg id']==chel]['номер набора'].tolist():
                df_corr[chel][set_no]=1
            else:
                df_corr[chel][set_no]=0

    df_corr = df_corr.astype(float)
    
    df2 = df_corr.corr()
    list_new_index = []
    df3 = df2[user_id].nlargest(n=4)[1:]
    list_scores_percent = []
    for i in df2[user_id].nlargest(n=4)[1:].index:
        percent = 0
        hamming_distance = hamming(df_corr[user_id], df_corr[i]) #доля попарно несовпадающих элементов
        percent = (1 - hamming_distance)*100
        list_scores_percent.append(percent)

    for i in df3.index:
        list_new_index.append(df[df['tg id']==i]['имя'].unique()[0])
    df3.index = list_new_index
    list_anon_index = []
    for i in df3.index:
        name = ''
        for j in range(len(i)):
            if j == 0 or j == len(i)-1:
                name += i[j]
            else:
                name += '*'
        list_anon_index.append(name)
    df3.index = list_anon_index
    
    text1 = 'Пользователи , похожие на вас:\n'
    for i in range(len(df3)):
        text1 += df3.index[i] + "    "+"{:.2f} %".format(list_scores_percent[i]) +'\n' 
    await message.reply(text1)



@dp.message_handler(filters.RegexpCommandsFilter(regexp_commands=['-([0-9]*)']))
async def delete_fav(message: types.Message, regexp_command):
    user_name = message.from_user.full_name
    user_id = message.from_user.id
    t = time.localtime()
    df = pd.read_csv('LEGOdata.csv')
    df = df.drop(df[(df['tg id']==user_id) & (df['номер набора']==int(regexp_command.group(1)))].index)
    df.to_csv('LEGOdata.csv',index=False)
    df = pd.read_csv('LEGOdata.csv')
    logging.info(f"{user_name=} {user_id=} sent message: {message.text} at {time.asctime(t)}")
    await message.reply("Вы удалили набор {} из избранного".format(regexp_command.group(1)))

@dp.message_handler(filters.RegexpCommandsFilter(regexp_commands=['\+([0-9]*)']))
async def add_fav(message: types.Message, regexp_command):
    user_name = message.from_user.full_name
    user_id = message.from_user.id
    t = time.localtime()
    t_formated = time.strftime('%d.%m.%Y г. %H:%M:%S', t)
    df = pd.read_csv('LEGOdata.csv')
    temp_df = pd.DataFrame({'имя':[user_name],'tg id':[user_id],'время':[t_formated],'номер набора':int(regexp_command.group(1)),'заметки':['']})
    temp_df.to_csv('temp_df.csv', index=False)
    df = pd.concat([df, temp_df])
    df.to_csv('LEGOdata.csv',index=False)
    await message.reply(text='Набор {} успешно добавлен в избранное. Вы можете просмотреть избранное командой /fav'.format(regexp_command.group(1)))

@dp.message_handler(filters.RegexpCommandsFilter(regexp_commands=['set_([0-9]*)']))
async def add_fav(message: types.Message, regexp_command):
    user_name = message.from_user.full_name
    user_id = message.from_user.id
    t = time.localtime()
    t_formated = time.strftime('%d.%m.%Y г. %H:%M:%S', t)
    logging.info(f"{user_name=} {user_id=} sent message: {message.text} at {time.asctime(t)}")

    set_number = regexp_command.group(1)
    temp_df = pd.DataFrame({'имя':[user_name],'tg id':[user_id],'время':[t_formated],'номер набора':[set_number],'заметки':['']})
    temp_df.to_csv('temp_df.csv', index=False)

    keyboard = create_keyboard(set_number, user_name, user_id, t)
    text1 = 'Набор '+ set_number 
    await message.answer(text1, reply_markup=keyboard)


@dp.message_handler(content_types=['photo'])
async def handle_docs_photo(message):
    user_name = message.from_user.full_name
    user_id = message.from_user.id
    t = time.localtime()
    t_formated = time.strftime('%d.%m.%Y г. %H:%M:%S', t)
    logging.info(f"{user_name=} {user_id=} sent message: {message.photo[-1]} at {time.asctime(t)}")

    await message.photo[-1].download('test.jpg')
    resize = T.Resize((1024, 800))
    img = resize(Image.open('test.jpg'))
    photo = open('test.jpg', 'rb')
    results = model(img)
    boxes = results[0].boxes
    pic_df = pd.DataFrame(boxes.data.cpu(), columns=['xmin','ymin','xmax','ymax','confidence','class'])
    pic_df['class'] = pic_df['class'].astype('int32')

    
    set_number = ''.join(i for i in pic_df[pic_df['class']<10].sort_values(by=['xmin'])['class'].astype('str').tolist())
    temp_df = pd.DataFrame({'имя':[user_name],'tg id':[user_id],'время':[t_formated],'номер набора':[set_number],'заметки':['']})
    temp_df.to_csv('temp_df.csv', index=False)
    

    keyboard = create_keyboard(set_number, user_name, user_id, t)
    text1 = 'Набор '+ set_number 
    await message.answer(text1, reply_markup=keyboard)

def create_keyboard(set_no, user_name, user_id, t):
    site1 = 'bricker.ru/sets/'+set_no+'/'
    site2 = 'https://www.lego.com/ru-ru/service/buildinginstructions/'+set_no
    site3 = 'https://www.brickeconomy.com/set/'+set_no+'-1/'
    text4 = 'btn4' 
    inline_kb = InlineKeyboardMarkup()
    inline_btn1 = InlineKeyboardButton('Информация о наборе', url=site1)
    inline_btn2 = InlineKeyboardButton('Инструкция', url=site2)
    inline_btn3 = InlineKeyboardButton('Прогноз роста цены', url=site3)
    inline_btn4 = InlineKeyboardButton('В избранное', callback_data=text4)
    inline_btn5 = InlineKeyboardButton('Сделать заметку', callback_data='btn5')

    inline_kb.add(inline_btn1)
    inline_kb.add(inline_btn2)
    inline_kb.add(inline_btn3)
    inline_kb.add(inline_btn4)
    inline_kb.add(inline_btn5)

    return inline_kb

@dp.callback_query_handler(lambda c: c.data and c.data.startswith('btn'))
async def process_callback_kb1btn1(callback_query: CallbackQuery):
    code = callback_query.data[3]
    temp_df = pd.read_csv('temp_df.csv') 
    if code.isdigit():
        code = int(code)
    if code == 4:
        df = pd.read_csv('LEGOdata.csv') 
        if temp_df['номер набора'][0] in (df[df['tg id']==temp_df['tg id'][0]]['номер набора'].tolist()):
            await bot.answer_callback_query(callback_query.id, 
                                        text='Набор уже был добавлен ранее. Вы можете просмотреть избранное командой /fav', show_alert=True)
        else:
            df = pd.concat([df, temp_df])
            df.to_csv('LEGOdata.csv',index=False)
            await bot.answer_callback_query(callback_query.id, 
                                        text='Набор успешно добавлен в избранное. Вы можете просмотреть избранное командой /fav', show_alert=True)
    elif code == 5:
        await bot.answer_callback_query(callback_query.id, text='Просто введите номер набора и через ПРОБЕЛ текст заметки (косая черта / не требуется)', show_alert=True)




@dp.message_handler(commands=['help'])
async def process_help_command(message: types.Message):
    help_message = ("Вы можете прислать боту картинку коробки или воспользоваться любой из следующих команд.\n\n"+
    "Доступные команды:\n\n"+
    "/set_0000 - введите номер набора в соответствии с примером , чтобы открыть информацию о нём , не присылая фото\n\n"
    "/start - приветствие\n\n"+
    "/fav - ваше избранное\n\n"+
    "/zam - ваши заметки\n\n"+
    "/+0000  -  введите косую черту , знак + и номер набора , чтобы быстро добавить его в избранное\n\n"+
    "/-0000  -  введите косую черту , знак - и номер набора , чтобы удалить его из избранного (заметка о нём также удалится!!!)\n\n"+
    "0000 этот набор весьма неплох - чтобы добавить заметку , введите номер набора (БЕЗ ЧЕРТЫ!!!) и через ПРОБЕЛ любые выши размышления о данном наборе\n\n"+
    "/vkus - пользователи , с похожими вкусами (имена частично скрыты для конфиденциальности)\n\n"+
    "/help - вернуться в список команд")
    

    await message.reply(help_message)


@dp.message_handler()
async def send_echo(message: types.Message):
    user_name = message.from_user.full_name
    user_id = message.from_user.id
    text = message.text
    set_no = text.split(' ')[0]
    if set_no.isdigit():
        notes = ' '.join(i for i in text.split(' ')[1:])
        t = time.localtime()
        t_formated = time.strftime('%d.%m.%Y г. %H:%M:%S', t)
        logging.info(f"{user_name=} {user_id=} sent message: {message.text} at {time.asctime(t)}")
        df.loc[len(df)] = [user_name, user_id, t_formated, set_no, notes]
        df.to_csv('LEGOdata.csv',index=False)
        await bot.send_message(user_id, 'Заметка добавлена. Вы можете просмотреть свои заметки командой /zam')

if __name__ == '__main__':
    executor.start_polling(dp)