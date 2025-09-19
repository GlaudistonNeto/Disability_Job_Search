import requests
from bs4 import BeautifulSoup
import json
import time
from datetime import datetime
import csv
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import schedule


class PCDJobSearch:
    def __init__(self):
        self.jobs_data = []
        self.seen_jobs = set()

    def search_vagas_br(self):
        """Search on Vagas.com.br for PCD positions in Aracaju"""
        try:
            url = "https://www.vagas.com.br/vagas-de-pcd-em-aracaju-se"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }

            print("Procurando vagas no Vagas.com.br...")
            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')
            job_listings = soup.find_all('li', class_='vaga')

            if not job_listings:
                print("Nenhuma vaga encontrada no Vagas.com.br")
                return

            print(f"Encontradas {len(job_listings)} vagas no Vagas.com.br")

            for job in job_listings:
                try:
                    title_elem = job.find('h2', class_='cargo')
                    company_elem = job.find('span', class_='emprVaga')
                    location_elem = job.find('span', class_='vaga-local')
                    link_elem = job.find('a', href=True)

                    if all([title_elem, company_elem, location_elem, link_elem]):
                        job_data = {
                            'title': title_elem.text.strip(),
                            'company': company_elem.text.strip(),
                            'location': location_elem.text.strip(),
                            'link': 'https://www.vagas.com.br' + link_elem['href'],
                            'source': 'Vagas.com.br',
                            'timestamp': datetime.now().isoformat(),
                            'pcd': True
                        }

                        job_id = f"{job_data['title']}_{job_data['company']}"
                        if job_id not in self.seen_jobs:
                            self.jobs_data.append(job_data)
                            self.seen_jobs.add(job_id)

                except Exception as e:
                    print(f"Erro processando vaga: {e}")
                    continue

        except requests.exceptions.RequestException as e:
            print(f"Erro acessando Vagas.com.br: {e}")
        except Exception as e:
            print(f"Erro inesperado no Vagas.com.br: {e}")

    def search_infojobs(self):
        """Search on InfoJobs for PCD positions"""
        try:
            url = "https://www.infojobs.com.br/vagas-de-emprego-pcd.aspx"
            params = {
                'province': 'Sergipe',
                'city': 'Aracaju'
            }

            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }

            print("Procurando vagas no InfoJobs...")
            response = requests.get(url, headers=headers, params=params, timeout=15)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')

            # Try different selectors for InfoJobs
            selectors = [
                'div.vaga',
                'article.vaga',
                'div.vaga-card',
                'li.vaga-item'
            ]

            job_listings = []
            for selector in selectors:
                found = soup.find_all(selector)
                if found:
                    job_listings = found
                    break

            if not job_listings:
                print("Nenhuma vaga encontrada no InfoJobs")
                return

            print(f"Encontradas {len(job_listings)} vagas no InfoJobs")

            for job in job_listings:
                try:
                    title_elem = job.find('h2') or job.find('a', class_='vagaTitle') or job.find('span', class_='title')
                    company_elem = job.find('span', class_='empresa') or job.find('div', class_='company') or job.find(
                        'span', class_='company')
                    location_elem = job.find('span', class_='cidade') or job.find('div', class_='location') or job.find(
                        'span', class_='location')
                    link_elem = job.find('a', href=True)

                    if title_elem and link_elem:
                        job_data = {
                            'title': title_elem.text.strip(),
                            'company': company_elem.text.strip() if company_elem else 'Não especificado',
                            'location': location_elem.text.strip() if location_elem else 'Aracaju, SE',
                            'link': link_elem['href'] if link_elem['href'].startswith(
                                'http') else 'https://www.infojobs.com.br' + link_elem['href'],
                            'source': 'InfoJobs',
                            'timestamp': datetime.now().isoformat(),
                            'pcd': True
                        }

                        job_id = f"{job_data['title']}_{job_data['company']}"
                        if job_id not in self.seen_jobs:
                            self.jobs_data.append(job_data)
                            self.seen_jobs.add(job_id)

                except Exception as e:
                    print(f"Erro processando vaga do InfoJobs: {e}")
                    continue

        except requests.exceptions.RequestException as e:
            print(f"Erro acessando InfoJobs: {e}")
        except Exception as e:
            print(f"Erro inesperado no InfoJobs: {e}")

    def search_government_portals(self):
        """Search government and institutional portals"""
        try:
            print("Verificando portais governamentais e institucionais...")

            # List of reliable government and institutional portals
            portals = [
                {
                    'name': 'Governo de Sergipe',
                    'url': 'https://www.se.gov.br',
                    'check_type': 'manual'
                },
                {
                    'name': 'Prefeitura de Aracaju',
                    'url': 'https://www.aracaju.se.gov.br',
                    'check_type': 'manual'
                },
                {
                    'name': 'Sine Sergipe',
                    'url': 'https://sinesergipe.se.gov.br',
                    'check_type': 'manual'
                }
            ]

            for portal in portals:
                try:
                    if portal['check_type'] == 'manual':
                        print(f"✓ {portal['name']}: {portal['url']} - Verifique manualmente a seção de vagas")
                    else:
                        headers = {
                            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                        }
                        response = requests.get(portal['url'], headers=headers, timeout=10)
                        if response.status_code == 200:
                            print(f"✓ {portal['name']} acessível: {portal['url']}")

                except requests.exceptions.RequestException:
                    print(f"✗ {portal['name']} não acessível no momento")
                except Exception as e:
                    print(f"Erro verificando {portal['name']}: {e}")

        except Exception as e:
            print(f"Erro na verificação de portais: {e}")

    def search_company_careers(self):
        """Suggest companies that often have PCD positions"""
        print("\nEmpresas em Aracaju que frequentemente oferecem vagas PCD:")
        companies = [
            "• Banco do Brasil",
            "• Caixa Econômica Federal",
            "• Correios",
            "• Petrobras",
            "• Eletrobras",
            "• Embrapa",
            "• Universidades Federais e Estaduais",
            "• Hospitais Públicos",
            "• Secretarias Estaduais e Municipais"
        ]

        for company in companies:
            print(company)

        print("\nDica: Verifique os sites de carreira dessas empresas regularmente!")

    def save_to_csv(self, filename="pcd_vagas_aracaju.csv"):
        """Save results to CSV file"""
        if not self.jobs_data:
            print("Nenhuma vaga para salvar no momento")
            return

        try:
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = ['title', 'company', 'location', 'link', 'source', 'timestamp', 'pcd']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

                writer.writeheader()
                for job in self.jobs_data:
                    writer.writerow(job)

            print(f"✓ Vagas salvas em {filename}")

        except Exception as e:
            print(f"Erro salvando CSV: {e}")

    def display_results(self):
        """Display results in console"""
        if not self.jobs_data:
            print("\nNenhuma vaga PCD encontrada no momento.")
            print("Recomendamos verificar os portais manualmente e cadastrar seu currículo nos sites das empresas.")
            return

        print(f"\n{'=' * 80}")
        print(f"VAGAS PCD ENCONTRADAS EM ARACAJU - {datetime.now().strftime('%d/%m/%Y %H:%M')}")
        print(f"{'=' * 80}")

        for i, job in enumerate(self.jobs_data, 1):
            print(f"\n{i}. {job['title']}")
            print(f"   Empresa: {job['company']}")
            print(f"   Local: {job['location']}")
            print(f"   Fonte: {job['source']}")
            print(f"   Link: {job['link']}")
            print(f"   {'-' * 60}")

    def run_search(self):
        """Run all search methods"""
        print(f"\n🔍 INICIANDO BUSCA DE VAGAS PCD - ARACAJU/SE")
        print(f"📅 {datetime.now().strftime('%d/%m/%Y %H:%M')}")
        print(f"{'=' * 60}")

        previous_jobs_count = len(self.seen_jobs)

        self.search_vagas_br()
        self.search_infojobs()
        self.search_government_portals()
        self.search_company_careers()

        new_jobs_count = len(self.jobs_data) - previous_jobs_count
        print(f"\n✅ BUSCA CONCLUÍDA: {new_jobs_count} nova(s) vaga(s) encontrada(s)")

        self.display_results()
        self.save_to_csv()

        return new_jobs_count


def main():
    # Initialize job search
    job_search = PCDJobSearch()

    # Run search immediately
    job_search.run_search()

    # Ask if user wants to schedule automatic searches
    print(f"\n{'=' * 60}")
    schedule_choice = input("Deseja agendar buscas automáticas? (s/n): ").lower().strip()

    if schedule_choice == 's':
        try:
            hours = int(input("Digite o intervalo em horas (ex: 6 para 6 horas): "))

            def scheduled_search():
                print(f"\n⏰ EXECUTANDO BUSCA AGENDADA - {datetime.now().strftime('%d/%m/%Y %H:%M')}")
                print(f"{'=' * 60}")
                job_search.run_search()

            # Schedule the search
            schedule.every(hours).hours.do(scheduled_search)

            print(f"\n⏰ MONITOR INICIADO: Verificando a cada {hours} horas...")
            print("🛑 Pressione Ctrl+C para parar")
            print(f"{'=' * 60}")

            # Run first scheduled search immediately
            scheduled_search()

            while True:
                schedule.run_pending()
                time.sleep(60)  # Check every minute

        except ValueError:
            print("❌ Intervalo inválido. Encerrando.")
        except KeyboardInterrupt:
            print("\n⏹️  Monitor encerrado pelo usuário.")
    else:
        print("\n✅ Busca única concluída. Verifique o arquivo 'pcd_vagas_aracaju.csv'")
        print("💡 Dica: Execute o programa regularmente para novas vagas!")


if __name__ == "__main__":
    main()