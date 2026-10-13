class Playlist:
    """Плейлист, который хранит песни в виде списка словарей."""

    def __init__(self):
        self.songs = []

    def add_song(self, name, duration):
        """Добавить песню с названием и продолжительностью в секундах."""
        self.songs.append({"name": name, "duration": duration})

    def remove_song(self, name):
        """Удалить первую песню с указанным названием.

        Возвращает True, если песня найдена, и False, если такой песни нет.
        """
        for song in self.songs:
            if song["name"] == name:
                self.songs.remove(song)
                return True
        return False

    def total_duration(self):
        """Вернуть общую продолжительность всех песен в секундах."""
        return sum(song["duration"] for song in self.songs)

    def __len__(self):
        """Вернуть количество песен для функции len(playlist)."""
        return len(self.songs)

    def show_songs(self):
        """Вернуть пронумерованный список песен для отображения пользователю."""
        if not self.songs:
            return "Плейлист пуст."

        lines = []
        for number, song in enumerate(self.songs, start=1):
            lines.append(f"{number}. {song['name']} — {song['duration']} сек.")
        return "\n".join(lines)


def main():
    """Показать работу всех методов класса Playlist."""
    playlist = Playlist()

    print("Пустой плейлист:")
    print(playlist.show_songs())
    print(f"Количество песен: {len(playlist)}")
    print(f"Общая продолжительность: {playlist.total_duration()} сек.\n")

    playlist.add_song("Bohemian Rhapsody", 354)
    playlist.add_song("Imagine", 183)
    playlist.add_song("Billie Jean", 294)

    print("После добавления нескольких песен:")
    print(playlist.show_songs())
    print(f"Количество песен: {len(playlist)}")
    print(f"Общая продолжительность: {playlist.total_duration()} сек.\n")

    if playlist.remove_song("Imagine"):
        print("Песня Imagine удалена.")
    print("Плейлист после удаления песни:")
    print(playlist.show_songs())
    print()

    if not playlist.remove_song("Несуществующая песня"):
        print("Песня 'Несуществующая песня' не найдена.")


if __name__ == "__main__":
    main()
