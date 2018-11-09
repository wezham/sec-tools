class EmailPermutor:

    def __init__(self, name, company_name):
        self.name = name;
        self.company_name = "@" + company_name;
        self.emails = []
        self.permute_over_names()
        self.print_emails()

    def permute_over_names(self):
        split_names = self.name.split(' ')
        try:
            first_name = split_names[0].lower()
            last_name = split_names[1].lower()
            self.mix_and_match(first_name, last_name)
        except:
            print("Name not formatted correctly. Try 'FIRSTNAME LASTNAME'")

    def mix_and_match(self, first_name, last_name):
        self.appender(first_name, None,last_name)
        self.appender(last_name, None,first_name)
        self.appender(first_name, ".", last_name)
        self.appender(last_name, ".", first_name)
        self.appender(first_name)
        self.appender(last_name)
        self.appender(first_name[:1], ".", last_name)
        self.appender(first_name[:1], None, last_name)
        self.appender(last_name,  None,first_name[:1])
        self.appender(last_name, ".", first_name[:1])

    def appender(self, half1, joiner="", half2=""):
        self.emails.append(half1+joiner+half2+self.company_name)

    def print_emails(self):
        for email in self.emails:
            print(email)

EmailPermutor("Wesley Hamburger", "hamskyandco")
